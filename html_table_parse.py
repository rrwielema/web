import pandas as pd
import warnings


def to_dataframe(table_html, has_headers=True, custom_headers=None):

    if has_headers:
        if custom_headers:
            headers = custom_headers
        else:
            headers = [h.text for h in table_html.select('th')]
        values = [row.select('td') for row in table_html.select('tr')[1:]]
    elif custom_headers:
        headers = custom_headers
        values = [row.select('td') for row in table_html.select('tr')]
    else:
        warnings.warn('Table contains no headers and no custom headers were supplied.\n'
              'Setting column names to col_1, col_2 ... col_n.', SyntaxWarning)
        values = [row.select('td') for row in table_html.select('tr')]
        headers = ['col_' + str(x) for x in range(1, len(values[2])+1)]
    rows = []
    for row in values:
        rows.append([f.text for f in row])

    try:
        df = pd.DataFrame(columns=headers, data=rows)
    except ValueError:
        cols = len(rows[0])
        custom_cols = len(headers)
        if cols < custom_cols:
            warnings.warn(f'Too many headers ({custom_cols}) given for the amount of columns ({cols}).\n'
                  f'Using first {cols} values: {", ".join(headers[:cols])}.', SyntaxWarning)
            df = pd.DataFrame(columns=headers[:cols], data=rows)
        else:
            warnings.warn(f'Too few headers ({custom_cols}) given for the amount of columns ({cols}).\n'
                          f'Adding col_n as column names for the remaining {cols - custom_cols} columns.',
                          SyntaxWarning)
            headers = headers + ['col_' + str(x) for x in range(custom_cols + 1, cols + 1)]
            df = pd.DataFrame(columns=headers, data=rows)

    return df
