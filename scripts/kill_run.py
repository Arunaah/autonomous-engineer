import psycopg2
conn = psycopg2.connect('postgresql://ae_user:ae_secure_pass_2024@localhost:5432/autonomous_engineer')
cur = conn.cursor()
cur.execute("UPDATE ae_runs SET status='error', error='killed - fix deployed' WHERE run_id=2")
conn.commit()
cur.close()
conn.close()
print('Run 2 killed in DB')
