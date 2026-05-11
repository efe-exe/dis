DIS exercise 01

2. Setup and usage of a relational database system

a) This implementation uses PostgreSQL with Python.

- For Ubuntu Linux install the following packages:
sudo apt install postgresql postgresql-contrib python3-psycopg2

- Install dependencies with pip: `pip install -r requirements.txt`

- The PostgreSQL DBMS exists as a daemon in Linux. 
- It can communicate with other processes (wait for connections). 
- By default it uses port 5432. To install/run it, execute the following from the command line:
sudo systemctl enable --now postgresql

- A user named 'postgres' is automatically created. An interactive session can be run like this:
sudo -u postgres psql

- To create a test database user and a database run the following commands from ithin the psql prompt:
CREATE USER Bob WITH PASSWORD 'bobbycar';
CREATE DATABASE dis_test_db OWNER Bob;



b) Experimenting with concurrent transactions from different connections



