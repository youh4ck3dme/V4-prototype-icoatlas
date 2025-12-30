"""
ERP Service Manager
Spravuje ERP pripojenia a synchronizácie
"""

from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session
from ..database import save_company_cache

from .models import ErpConnection, ErpConnectionStatus, ErpSyncLog, ErpType
from .money_s3_connector import MoneyS3Connector
from .pohoda_connector import PohodaConnector
from .sap_connector import SapConnector


def get_connector(erp_type: ErpType, connection_data: Dict):
    """Vytvorí správny connector podľa typu ERP"""
    if erp_type == ErpType.POHODA:
        return PohodaConnector(connection_data)
    elif erp_type == ErpType.MONEY_S3:
        return MoneyS3Connector(connection_data)
    elif erp_type == ErpType.SAP:
        return SapConnector(connection_data)
    else:
        raise ValueError(f"Unknown ERP type: {erp_type}")


def create_erp_connection(
    db: Session, user_id: int, erp_type: ErpType, connection_data: Dict
) -> ErpConnection:
    """Vytvorí nové ERP pripojenie"""
    connection = ErpConnection(
        user_id=user_id,
        erp_type=erp_type,
        connection_data=connection_data,
        status=ErpConnectionStatus.INACTIVE,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


def test_erp_connection(erp_type: ErpType, connection_data: Dict) -> Dict:
    """Testuje ERP pripojenie"""
    try:
        connector = get_connector(erp_type, connection_data)
        result = connector.test_connection()
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "error": str(e),
        }


def activate_erp_connection(db: Session, connection_id: int, user_id: int) -> bool:
    """Aktivuje ERP pripojenie"""
    connection = (
        db.query(ErpConnection)
        .filter(ErpConnection.id == connection_id, ErpConnection.user_id == user_id)
        .first()
    )

    if not connection:
        return False

    # Test pripojenia
    test_result = test_erp_connection(connection.erp_type, connection.connection_data)

    if test_result.get("success"):
        connection.status = ErpConnectionStatus.ACTIVE

        # Získať info o firme
        connector = get_connector(connection.erp_type, connection.connection_data)
        company_info = connector.get_company_info()

        if "error" not in company_info:
            connection.company_name = company_info.get("company_name")
            connection.company_id = company_info.get("company_id")

        db.commit()
        return True
    else:
        connection.status = ErpConnectionStatus.ERROR
        db.commit()
        return False


def deactivate_erp_connection(db: Session, connection_id: int, user_id: int) -> bool:
    """Deaktivuje ERP pripojenie"""
    connection = (
        db.query(ErpConnection)
        .filter(ErpConnection.id == connection_id, ErpConnection.user_id == user_id)
        .first()
    )

    if not connection:
        return False

    connection.status = ErpConnectionStatus.INACTIVE
    connection.sync_enabled = False
    db.commit()
    return True


def get_user_erp_connections(db: Session, user_id: int) -> List[ErpConnection]:
    """Získa všetky ERP pripojenia používateľa"""
    return (
        db.query(ErpConnection)
        .filter(ErpConnection.user_id == user_id)
        .order_by(ErpConnection.created_at.desc())
        .all()
    )


def sync_erp_data(
    db: Session, connection_id: int, user_id: int, sync_type: str = "incremental"
) -> Dict:
    """Synchronizuje dáta z ERP"""
    connection = (
        db.query(ErpConnection)
        .filter(ErpConnection.id == connection_id, ErpConnection.user_id == user_id)
        .first()
    )

    if not connection:
        return {"success": False, "message": "Connection not found"}

    if connection.status != ErpConnectionStatus.ACTIVE:
        return {"success": False, "message": "Connection is not active"}

    # Vytvoriť sync log
    sync_log = ErpSyncLog(
        connection_id=connection_id,
        sync_type=sync_type,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(sync_log)
    db.commit()

    try:
        connector = get_connector(connection.erp_type, connection.connection_data)

        # Synchronizovať dodávateľov
        suppliers = connector.get_suppliers(limit=1000)
        records_synced = len(suppliers)
        records_failed = 0

        # Save each supplier to cache (or DB) using CompanyCache helper
        for supplier in suppliers:
            try:
                identifier = supplier.get("identifier") or supplier.get("ico") or supplier.get("id")
                if not identifier:
                    continue
                save_company_cache(
                    identifier=identifier,
                    country=connection.erp_type.name,  # simplistic mapping; adjust as needed
                    company_name=supplier.get("name", ""),
                    data=supplier,
                    risk_score=None,
                    expires_hours=24,
                )
            except Exception as e:
                records_failed += 1
                # Optionally log the error; for now we just count failures

        sync_log.status = "success"
        sync_log.records_synced = records_synced
        sync_log.records_failed = records_failed
        sync_log.completed_at = datetime.utcnow()
        sync_log.duration_seconds = int(
            (sync_log.completed_at - sync_log.started_at).total_seconds()
        )

        connection.last_sync_at = datetime.utcnow()

        # Nastaviť ďalšiu synchronizáciu
        if connection.sync_frequency == "daily":
            connection.next_sync_at = datetime.utcnow() + timedelta(days=1)
        elif connection.sync_frequency == "weekly":
            connection.next_sync_at = datetime.utcnow() + timedelta(weeks=1)

        db.commit()

        return {
            "success": True,
            "message": "Sync completed",
            "records_synced": records_synced,
            "records_failed": records_failed,
            "sync_log_id": sync_log.id,
        }
    except Exception as e:
        sync_log.status = "error"
        sync_log.error_message = str(e)
        sync_log.completed_at = datetime.utcnow()
        sync_log.duration_seconds = int(
            (sync_log.completed_at - sync_log.started_at).total_seconds()
        )
        db.commit()

        return {"success": False, "message": f"Sync failed: {str(e)}", "error": str(e)}


def get_supplier_payment_history_from_erp(
    db: Session, connection_id: int, user_id: int, supplier_ico: str, days: int = 365
) -> List[Dict]:
    """Získa históriu platieb dodávateľa z ERP"""
    connection = (
        db.query(ErpConnection)
        .filter(
            ErpConnection.id == connection_id,
            ErpConnection.user_id == user_id,
            ErpConnection.status == ErpConnectionStatus.ACTIVE,
        )
        .first()
    )

    if not connection:
        return []

    try:
        connector = get_connector(connection.erp_type, connection.connection_data)
        return connector.get_supplier_payment_history(supplier_ico, days)
    except Exception as e:
        print(f"Error getting payment history: {e}")
        return []


def get_erp_sync_logs(
    db: Session, connection_id: int, user_id: int, limit: int = 50
) -> List[ErpSyncLog]:
    """Získa logy synchronizácií"""
    connection = (
        db.query(ErpConnection)
        .filter(ErpConnection.id == connection_id, ErpConnection.user_id == user_id)
        .first()
    )

    if not connection:
        return []

    return (
        db.query(ErpSyncLog)
        .filter(ErpSyncLog.connection_id == connection_id)
        .order_by(ErpSyncLog.started_at.desc())
        .limit(limit)
        .all()
    )
