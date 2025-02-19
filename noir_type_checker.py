from typing import Any, Optional, Dict, List, Union
from noir_lexer import TokenType
from noir_types import TypeAnnotation, TypeParameter, TypeKind

class TypeError(Exception):
    """Exception raised for type errors."""
    pass

class GenericTypeChecker:
    """Handles validation and checking of generic types."""
    
    @staticmethod
    def validate_type_parameters(type_annotation: TypeAnnotation, type_checker: 'TypeChecker') -> None:
        """Validate that type parameters satisfy their constraints."""
        if not type_annotation.parameters:
            return
            
        for param in type_annotation.parameters:
            if isinstance(param, TypeParameter):
                continue  # Skip checking uninstantiated parameters
            if isinstance(param, TypeAnnotation):
                # Recursively validate nested generic types
                GenericTypeChecker.validate_type_parameters(param, type_checker)

    @staticmethod
    def is_valid_instantiation(generic: TypeAnnotation, instance: TypeAnnotation) -> bool:
        """Check if a generic type is correctly instantiated."""
        if not generic.is_generic() or not instance.is_instantiated():
            return False
            
        if generic.name != instance.name:
            return False
            
        if len(generic.parameters) != len(instance.parameters):
            return False
            
        # Check that all type parameters are properly instantiated
        for param, arg in zip(generic.parameters, instance.parameters):
            if isinstance(param, TypeParameter):
                if not isinstance(arg, TypeAnnotation):
                    return False
                if not param.is_satisfied_by(arg, TypeChecker):
                    return False
            elif isinstance(param, TypeAnnotation):
                if not isinstance(arg, TypeAnnotation):
                    return False
                if not GenericTypeChecker.is_valid_instantiation(param, arg):
                    return False
                    
        return True

class TypeChecker:
    def __init__(self):
        self.generic_checker = GenericTypeChecker()
        self._subtype_relations = {
            "Int": {"Float", "Double"},
            "Float": {"Double"},
            "Char": {"String"}  # A Char can be implicitly converted to String
        }

    def is_subtype(self, sub_type: str, super_type: str) -> bool:
        """Check if sub_type is a subtype of super_type."""
        if sub_type == super_type:
            return True
        return super_type in self._subtype_relations.get(sub_type, set())

    @staticmethod
    def can_implicitly_convert(from_type: str, to_type: str) -> bool:
        """Check if a type can be implicitly converted to another type."""
        # Allow implicit conversion from Int to Float/Double and Char to String
        if from_type == "Int":
            return to_type in ["Float", "Double"]
        elif from_type == "Char":
            return to_type == "String"
        return False

    @staticmethod
    def can_explicitly_convert(from_type: str, to_type: str, value: Any) -> bool:
        """Check if a type can be explicitly converted to another type."""
        # Allow casting between the same types
        if from_type == to_type:
            return True
        # Allow casting between numeric types
        if from_type in ["Float", "Double"] and to_type in ["Float", "Double", "Int"]:
            return True
        elif from_type == "String" and to_type == "Int":
            # Check if string contains only digits
            return str(value).strip('-').isdigit()
        elif from_type == "String" and to_type == "Float":
            # Check if string represents a valid float
            try:
                float(value)
                return True
            except ValueError:
                return False
        elif from_type == "String" and to_type == "Char":
            # Check if string is exactly one character
            return len(str(value)) == 1
        elif from_type in ["Int", "Float", "Double"] and to_type == "Bool":
            return True  # Allow numeric to boolean conversion
        return False

    @staticmethod
    def convert_value(value: Any, from_type: str, to_type: str) -> Any:
        """Convert a value from one type to another."""
        try:
            if to_type == "Int":
                return int(float(value))  # Handle both string and float conversion
            elif to_type == "Float":
                return float(value)
            elif to_type == "Double":
                return float(value)  # Python's float is double-precision by default
            elif to_type == "String":
                return str(value)
            elif to_type == "Char":
                # For Char type, ensure it's a single character
                str_val = str(value)
                if len(str_val) != 1:
                    raise TypeError(f"Cannot convert string of length {len(str_val)} to Char")
                return str_val
            elif to_type == "Bool":
                if isinstance(value, (int, float)):
                    return bool(value)  # 0 becomes False, non-zero becomes True
                elif isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes']
                return bool(value)
        except (ValueError, TypeError) as e:
            raise TypeError(f"Cannot convert {value} from {from_type} to {to_type}: {str(e)}")
        
        raise TypeError(f"Unsupported type conversion from {from_type} to {to_type}")

    @staticmethod
    def get_type_name(value: Any) -> str:
        """Get the type name of a value."""
        if isinstance(value, int):
            return "Int"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, str):
            # If it's a string of length 1, it's a Char
            if len(value) == 1:
                return "Char"
            return "String"
        elif isinstance(value, bool):
            return "Bool"
        return "Unknown"

    def validate_assignment(self, target_type: TypeAnnotation, value: Any, value_type: TypeAnnotation) -> Any:
        """Validate and possibly convert a value for assignment."""
        # Handle generic type assignments
        if target_type.is_generic() or target_type.is_instantiated():
            if not isinstance(value_type, TypeAnnotation):
                raise TypeError(f"Cannot assign non-generic type to generic type {target_type.name}")
            
            # Validate the generic type instantiation
            self.generic_checker.validate_type_parameters(target_type, self)
            if value_type.is_instantiated():
                self.generic_checker.validate_type_parameters(value_type, self)
            
            # Check if the types are compatible
            if not self.are_types_compatible(target_type, value_type):
                raise TypeError(f"Cannot assign value of type {value_type.name} to variable of type {target_type.name}")
            
            return value

        # Handle primitive type assignments
        if target_type.is_primitive() and value_type.is_primitive():
            if target_type.name == value_type.name:
                return value
                
            # Check for implicit conversion, subtype relationship, or boolean conversion
            if (self.can_implicitly_convert(value_type.name, target_type.name) or 
                self.is_subtype(value_type.name, target_type.name) or 
                (target_type.name == "Bool" and value_type.name in ["Int", "Float", "Double"])):
                return self.convert_value(value, value_type.name, target_type.name)
                
            raise TypeError(f"Cannot assign value of type {value_type.name} to variable of type {target_type.name}")
        
        raise TypeError("Invalid type annotations")

    def are_types_compatible(self, target_type: TypeAnnotation, value_type: TypeAnnotation) -> bool:
        """Check if two types are compatible for assignment."""
        # Same type
        if target_type.name == value_type.name:
            # If both are generic/instantiated, check parameters
            if target_type.is_generic() or target_type.is_instantiated():
                if not value_type.is_generic() and not value_type.is_instantiated():
                    return False
                return self.generic_checker.is_valid_instantiation(target_type, value_type)
            return True
            
        # Check for implicit conversion or subtype relationship
        if target_type.is_primitive() and value_type.is_primitive():
            return (self.can_implicitly_convert(value_type.name, target_type.name) or
                   self.is_subtype(value_type.name, target_type.name))
                   
        return False

    def validate_type_cast(self, value: Any, from_type: Union[str, TypeAnnotation], to_type: Union[str, TypeAnnotation]) -> Any:
        """Validate and perform an explicit type cast."""
        # Convert string types to TypeAnnotation if needed
        if isinstance(from_type, str):
            from_type = TypeAnnotation(from_type, kind=TypeKind.PRIMITIVE)
        if isinstance(to_type, str):
            to_type = TypeAnnotation(to_type, kind=TypeKind.PRIMITIVE)

        # Handle generic type casts
        if to_type.is_generic() or from_type.is_generic():
            if not self.generic_checker.is_valid_instantiation(from_type, to_type):
                raise TypeError(f"Cannot cast from {from_type.name} to {to_type.name}")
            return value

        # Handle primitive type casts
        if from_type.is_primitive() and to_type.is_primitive():
            if not self.can_explicitly_convert(from_type.name, to_type.name, value):
                raise TypeError(f"Cannot cast value {value} from {from_type.name} to {to_type.name}")
            return self.convert_value(value, from_type.name, to_type.name)

        raise TypeError(f"Unsupported type cast from {from_type.name} to {to_type.name}") 