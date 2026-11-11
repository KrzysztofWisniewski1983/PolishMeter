
def read_db_value(connection, indicator_name):
    cursor = connection.cursor()

    cursor.execute(
        "SELECT value FROM statistics_data WHERE name = ?",
        (indicator_name,)
    )

    result = cursor.fetchone()

    assert result is not None, f"Not found: {indicator_name}"

    return result[0]
