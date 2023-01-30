# Безопасное преобразование к основным типам данных
def safe_cast(raw_input, data_type):
    try:
        match data_type:
            case "str":
                return str(raw_input)
            case "int":
                return int(raw_input)
            case "float":
                return float(raw_input)
            case _:
                print("Указан несуществующий тип данных!")
                return -251
    except TypeError:
        print("Невозможно преобразовать тип данных!")
        return -252
    except ValueError:
        print("Данное значение не поддерживается!")
        return -253


# Безопасный ввод с указанием требуемого типа данных
def safe_input(prompt, data_type, retry):
    cast_input = None
    while cast_input is None:
        raw_input = input(prompt)
        if retry is False:
            cast_input = safe_cast(raw_input, data_type)
        else:
            retries = 0
            while cast_input is None or cast_input < -250:
                retries += 1
                if retries < 2:
                    cast_input = safe_cast(raw_input, data_type)
                else:
                    cast_input = safe_cast(input(prompt), data_type)
    return cast_input
