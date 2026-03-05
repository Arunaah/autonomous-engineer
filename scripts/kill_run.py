import psycopg2, sys
run_id = int(sys.argv[1]) if len(sys.argv) > 1 else 3
conn = psycopg2.connect('postgresql://ae_user:ae_secure_pass_2024@localhost:5432/autonomous_engineer')
cur = conn.cursor()
cur.execute("UPDATE ae_runs SET status=%s, error=%s WHERE run_id=%s",
            ('error', 'killed by operator', run_id))
conn.commit(); cur.close(); conn.close()
print(f'Run {run_id} killed')
