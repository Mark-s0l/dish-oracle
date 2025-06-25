from django.core.validators import RegexValidator

fields_name_validator = RegexValidator(
    regex=r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\s]*$",
    message="Название должно начинаться с буквы и содержать только буквы и пробелы",
)

ean13_validator = RegexValidator(
    regex=r"^\d{13}$", message="EAN-13 должен состоять из 13 цифр"
)

slug_validator = RegexValidator(regex=r"^[a-zA-Zа-яА-ЯёЁ\s]+$")
