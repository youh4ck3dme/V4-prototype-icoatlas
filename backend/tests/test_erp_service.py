"""
Tests for ERP service - simplified to avoid complex model dependencies
"""
import pytest
from unittest import mock

def test_get_connector_pohoda():
    """Test that get_connector returns correct connector type"""
    from services.erp.erp_service import get_connector
    from services.erp.models import ErpType
    from services.erp.pohoda_connector import PohodaConnector
    
    connector = get_connector(ErpType.POHODA, {"host": "test"})
    assert isinstance(connector, PohodaConnector)

def test_get_connector_money_s3():
    """Test that get_connector returns correct connector type"""
    from services.erp.erp_service import get_connector
    from services.erp.models import ErpType
    from services.erp.money_s3_connector import MoneyS3Connector
    
    connector = get_connector(ErpType.MONEY_S3, {"path": "test"})
    assert isinstance(connector, MoneyS3Connector)

def test_get_connector_sap():
    """Test that get_connector returns correct connector type"""
    from services.erp.erp_service import get_connector
    from services.erp.models import ErpType
    from services.erp.sap_connector import SapConnector
    
    connector = get_connector(ErpType.SAP, {"url": "test"})
    assert isinstance(connector, SapConnector)

def test_get_connector_unknown_raises():
    """Test that get_connector raises for unknown type"""
    from services.erp.erp_service import get_connector
    
    with pytest.raises(ValueError, match="Unknown ERP type"):
        get_connector("UNKNOWN", {})

def test_test_erp_connection_failure():
    """Test that test_erp_connection handles exceptions"""
    from services.erp import erp_service
    from services.erp.models import ErpType
    
    # Mock get_connector to raise an exception
    with mock.patch.object(erp_service, 'get_connector', side_effect=Exception("Connection failed")):
        result = erp_service.test_erp_connection(ErpType.POHODA, {})
        assert result["success"] is False
        assert "Connection failed" in result["message"]
