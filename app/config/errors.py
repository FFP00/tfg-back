def human_error(e: Exception) -> str:
    msg = str(e).lower()

    if "unique" in msg or "duplicate" in msg or "already exists" in msg:
        if "name" in msg:
            return "Ya existe un registro con ese nombre."
        if "support_email" in msg:
            return "Ese email de soporte ya está registrado."
        if "email" in msg:
            return "Ese email ya está registrado."
        if "code" in msg:
            return "Ese código ya está en uso."
        if "website_url" in msg:
            return "Esa URL de web ya está registrada."
        if "token" in msg:
            return "El token ya existe."
        return "Ya existe un registro con esos datos."

    if "foreign key" in msg or "violates foreign key" in msg:
        return "No se puede completar la operación: hay registros relacionados que lo impiden."

    if "not null" in msg or "null value" in msg:
        return "Hay campos obligatorios sin rellenar."

    if "check constraint" in msg or "violates check" in msg:
        if "balance" in msg:
            return "El balance no puede ser negativo."
        if "status" in msg:
            return "El estado no es válido."
        if "order" in msg or "customer_user_id" in msg:
            return "Error interno de ordenación de amistad."
        return "Un valor no cumple las restricciones permitidas."

    if "invalid input" in msg or "invalid literal" in msg or "invalid date" in msg:
        return "Formato incorrecto. Revisa fechas y campos numéricos."

    if "does not exist" in msg:
        return "El registro no existe."

    if "permission denied" in msg:
        return "No tienes permisos para realizar esta acción."

    if "division by zero" in msg:
        return "Error de cálculo: división por cero."

    return "Ha ocurrido un error inesperado. Inténtalo de nuevo."
