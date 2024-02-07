from line_apis import tab_get_lines, make_lines_dict
from multi_query_apis import tab_multi_margin_sweep


if __name__ == '__main__':

    _, lines = tab_get_lines('Detroit%20v%20Orlando')

    results = tab_multi_margin_sweep(make_lines_dict(lines))

    print(results)