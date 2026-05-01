import sqlite3


def clone_db(db_path):
	mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
	mem_curs = mem_conn.cursor()

	# Attach file database to mem database
	query = 'ATTACH ? AS DF'
	mem_curs.execute(query, [db_path])

	# Create table Users
	mem_curs.execute('''
	CREATE TABLE "Users" (
	"userName"	TEXT NOT NULL UNIQUE,
	"userId"	INTEGER NOT NULL,
	"status"	INTEGER NOT NULL DEFAULT 1,
	PRIMARY KEY("userName"))
	''')

	# Create table Groups
	mem_curs.execute('''
	CREATE TABLE "Groups" (
	"groupName"	TEXT NOT NULL UNIQUE,
	"groupId"	INTEGER NOT NULL,
	"PI"	TEXT ,
	PRIMARY KEY("groupName"))
	''')

	# Create table Group_Member
	mem_curs.execute('''
	CREATE TABLE "Group_Member" (
	"userName"	TEXT NOT NULL,
	"groupName"	TEXT NOT NULL,
	"dateIn"	INTEGER DEFAULT 0,
	"dateOut"	INTEGER DEFAULT 9999999999,
	FOREIGN KEY("userName") REFERENCES "Users"("userName"),
	FOREIGN KEY("groupName") REFERENCES "Groups"("groupName"))
	''')

	# Create table lsfjobs
	mem_curs.execute('''
	CREATE TABLE lsfjobs (
	jobId				INT,
	userId				INT,
	userName			TEXT,
	numAllocSlots		INT,
	allocSlotsStr       TEXT,
	submitTime			INT,
	startTime			INT,
	endTime				INT,
	queue				TEXT,
	idx					INT,
	maxRMem				INT,
	PRIMARY KEY (jobId, idx, startTime),
	FOREIGN KEY("userName") REFERENCES "Users"("userName")
	)
	''')

	# Create table Queues
	mem_curs.execute('''
	CREATE TABLE "Queues" (
	changeId			INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	startDate			INTEGER NOT NULL,
	endDate				INTEGER NOT NULL,
	general				INTEGER NOT NULL,
	long				INTEGER NOT NULL,
	high				INTEGER NOT NULL,
	training			INTEGER NOT NULL,
	gpu					INTEGER NOT NULL,
	total				INTEGER NOT NULL
	)
	''')

	# Insert data into mem tables
	mem_curs.execute('INSERT INTO Users SELECT * FROM DF.Users')
	mem_curs.execute('INSERT INTO Groups SELECT * FROM DF.Groups')
	mem_curs.execute('INSERT INTO Group_Member SELECT * FROM DF.Group_Member')
	mem_curs.execute('INSERT INTO Queues SELECT * FROM DF.Queues')
	mem_curs.execute('''
	INSERT INTO lsfJobs SELECT
	jobId,
	userId,
	userName,
	numAllocSlots,
	allocSlotsStr,
	submitTime,
	startTime,
	endTime,
	queue,
	idx,
	maxRMem
	FROM DF.lsfJobs
	''')

	mem_conn.commit()
	# Detach the file database
	mem_curs.execute('DETACH DATABASE DF')
	mem_conn.commit()
	return mem_conn

