from sql_to_mongo import sql_select_to_mongo

sql_query = """
SELECT name, age
FROM employees
WHERE age >= 25 AND department = 'Sales'
GROUP BY department
ORDER BY age DESC, name ASC
LIMIT 100;
"""

mongo_obj = sql_select_to_mongo(sql_query)
print(mongo_obj)

# Should Output:
# {
#   'collection': 'employees',
#   'find': {
#       'age': {'$gte': 25},
#       'department': 'Sales'
#   },
#   'projection': {'name': 1, 'age': 1},
#   'sort': [('age', -1), ('name', 1)],
#   'limit': 100,
#   'group': {
#       '$group': {
#           '_id': { 'department': '$department' },
#           'count': { '$sum': 1 }
#       }
#   }
# }
