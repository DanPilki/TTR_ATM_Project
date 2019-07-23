import sqlite3

conn = sqlite3.connect('data.db')

c = conn.cursor()

# c.execute("""CREATE TABLE accounts (pin TEXT PRIMARY KEY,checking DOUBLE,savings DOUBLE)""")

# c.execute("DELETE FROM accounts")

# c.execute("""DROP TABLE accounts""")

conn.commit()

conn.close()
