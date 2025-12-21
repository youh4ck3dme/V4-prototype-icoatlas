#!/usr/bin/env python3
"""
JSON Template Validator
Validates example JSON files against their respective schemas
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("❌ jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


def validate_template(schema_path: Path, example_path: Path) -> bool:
    """Validate an example JSON against its schema."""
    try:
        # Load schema
        with open(schema_path) as f:
            schema = json.load(f)
        
        # Load example
        with open(example_path) as f:
            example = json.load(f)
        
        # Validate
        jsonschema.validate(instance=example, schema=schema)
        print(f"✅ {example_path.name} is valid against {schema_path.name}")
        return True
        
    except jsonschema.ValidationError as e:
        print(f"❌ {example_path.name} validation error:")
        print(f"   {e.message}")
        print(f"   Path: {' -> '.join(str(p) for p in e.path)}")
        return False
    except Exception as e:
        print(f"❌ Error validating {example_path.name}: {e}")
        return False


def main():
    """Validate all example files."""
    templates_dir = Path(__file__).parent / "backend" / "services" / "templates"
    examples_dir = templates_dir / "examples"
    
    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        sys.exit(1)
    
    countries = ["sk", "cz", "pl", "hu"]
    all_valid = True
    
    print("🔍 Validating JSON templates...\n")
    
    for country in countries:
        schema_path = templates_dir / f"{country}_template.json"
        example_path = examples_dir / f"{country}_example.json"
        
        if not schema_path.exists():
            print(f"⚠️  Schema not found: {schema_path}")
            all_valid = False
            continue
            
        if not example_path.exists():
            print(f"⚠️  Example not found: {example_path}")
            all_valid = False
            continue
        
        if not validate_template(schema_path, example_path):
            all_valid = False
    
    print()
    if all_valid:
        print("✅ All templates validated successfully!")
        return 0
    else:
        print("❌ Some templates failed validation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
