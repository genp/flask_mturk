# flask_mturk
Setting up a Flask Webserver (with database backend) for creating AMT (Amazon Mechanical Turk) External Hits



# During setup, change these files to enable remote connections to postgres server and restart postgresql
# pg_hba.conf -- add lines
host    all             all             <remote host>         md5
#postgresql.conf
listen_addresses = '*'