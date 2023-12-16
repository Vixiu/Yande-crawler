def get_year_months(sy, sm, ey, em):
    while (sy, sm) <= (ey, em):


        if sm == 12:
            sy += 1
            sm = 1
        else:
            sm += 1



# 示例用法
start_year = 2022
start_month = 5
end_year = 2023
end_month = 8

year_months = get_year_months(start_year, start_month, end_year, end_month)
print(year_months)
