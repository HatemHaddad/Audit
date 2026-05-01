# -*- coding: utf-8 -*-
# from _plotly_future_ import timezones
import dash
import dash_core_components as dcc
import dash_table
import dash_table.FormatTemplate as FormatTemplate
import dash_html_components as html
from dash.dependencies import Input, Output
import flask
import os
import plotly.figure_factory as ff
import plotly.graph_objs as go
import sys
import pandas as pd
# import xlsxwriter
from datetime import datetime as dt
from datetime import timedelta
import pytz
# import sqlite3
import time
import db
# https://www.w3schools.com/cssref/css_colors.asp
color_palette = [
	'#1F77B4',
	'#FF7F0E',
	'#2CA02C',
	'#D62728',
	'#9467BD',
	'#8C564B',
	'#E377C2',
	'#7F7F7F',
	'#BCBD22',
	'#17BECF',
	'#57A9E2',
	'#FFB574',
	'#5FD35F',
	'#E77C7C',
	'#C6AEDC',
	'#BC8B81',
	'#F4CCE8',
	'#B2B2B2',
	'#E2E362',
	'#5FE0ED',
	'#103D5D',
	'#A74E00',
	'#165016',
	'#801718',
	'#613A84',
	'#4A2D27',
	'#CA2A99',
	'#4C4C4C',
	'#666712',
	'#0D6A73'
]
idle_color = '#778899'
rest_color = '#FFF0F5'
tz = pytz.timezone('Asia/Dubai')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

jsonPath = sys.argv[1]
df_config = pd.read_json(jsonPath)
selected_cluster = 'MI'
db_file = df_config[selected_cluster].database
print(db_file)
MEM_DB = db.clone_db(db_file)


def create_info_table(selected_cluster, df_config):
	df_queues = pd.DataFrame(df_config[selected_cluster]['queues'])
	info_table = html.Div(  # Beginning division of table
		children=[
			dash_table.DataTable(
				id='table',
				columns=[
					{"name": 'Queue Name', "id": 'name'},
					{"name": 'Architecture', "id": 'architecture'},
					{"name": 'Number of Nodes', "id": 'nNodes'},
					{"name": 'Cores per Node', "id": 'coresPerNode'},
					{"name": 'Description', "id": 'description'}
				],
				data=df_queues.to_dict('records'),
			)
		],
		style={'width': '80%', 'padding-left': '10%', 'padding-right': '10%'}
	)  # End division of table
	return info_table


def create_group_list_table(database):
	# cnx = sqlite3.connect(database)
	cnx = database
	df_groups = pd.read_sql_query("SELECT * FROM Groups ORDER BY groupName ASC", cnx)
	info_table = html.Div(  # Beginning division of table
		children=[
			dash_table.DataTable(
				columns=[
					{"name": 'Group Name', "id": 'groupName'},
					{"name": 'Group ID', "id": 'groupId'},
					{"name": 'Principal Investigator', "id": 'PI'}
				],
				data=df_groups.to_dict('records'),
			)
		],
		style={'width': '80%', 'padding-left': '10%', 'padding-right': '10%'}
	)  # End division of table
	return info_table


def create_group_stats_dropdown(database):
	cnx = database
	df_groups = pd.read_sql_query("SELECT groupName FROM Groups ORDER BY groupName ASC", cnx)
	options = [{'label': i, 'value': i} for i in df_groups['groupName']]
	return options


def create_group_ranking_queue_dropdown(queues):
	df_queues = pd.DataFrame(queues)
	options = [{'label': i, 'value': i} for i in df_queues['name']]
	return options

def get_queue_avail_time(database, queue, coresPerNode, start, end):
	cnx = database
	curs = cnx.cursor()
	query = '''SELECT total(availTime*(%s)) as availTimeQueue
		FROM(SELECT *,(MIN(endDate, ?) - MAX(startDate, ?)) as availTime
		FROM Queues
		WHERE availTime>0)''' % queue
	print(query)
	curs.execute(query, [end, start])
	queue_total_avail_time = float(curs.fetchall()[0][0]) * coresPerNode
	return queue_total_avail_time

def create_group_stats_gantt(database, selected_group, s_date, e_date):
	# print(database)
	print(selected_group)
	start_date = int(s_date.timestamp())
	end_date = int(e_date.timestamp())
	print(start_date)
	print(end_date)

	# Collect information from the database
	query = '''
	SELECT userName as Task, 
	datetime(MAX(dateIn, {}), 'unixepoch', 'localtime') as Start,
	datetime(MIN(dateOut, {}),'unixepoch','localtime') as Finish
	FROM Group_Member
	WHERE groupName = "{}" and Start < Finish
	'''.format(start_date, end_date, selected_group)
	cnx = database
	df_groups = pd.read_sql_query(query, cnx)

	print(df_groups.to_dict('records'))
	fig = ff.create_gantt(df_groups)
	fig['layout'].update(autosize=False, width=1250, margin=dict(l=110))
	gantt = html.Div(  # Beginning division of gant
		children=[
			dcc.Graph(
				figure=fig,
				id='gantt'
			)
		],
		style={'width': '80%', 'padding-left': '10%', 'padding-right': '10%'}
	)
	return gantt


def calculate_core_hours(row):
	# return min(row['endTime'], row['end_period']) - max(row['startTime'], row['start_period'])
	return (min(row['endTime'], row['end_period']) - max(row['startTime'], row['start_period']))*(row['numAllocSlots'])\
		/ 3600.0



def create_group_stats_area(database, cluster, selected_group, s_date, e_date):

	# calculate totalCores
	total_cores = 0
	for q in cluster.queues:
		total_cores = total_cores+(q['coresPerNode']*q['nNodes'])
	print(total_cores)
	print(cluster)
	# print(database)
	print(selected_group)
	print(s_date)
	print(e_date)
	start_date = int(s_date.timestamp())
	end_date = int(e_date.timestamp())
	print(start_date)
	print(end_date)

	cnx = database
	curs = cnx.cursor()
	# query = '''SELECT total(availTime*(total)) as availTimeQueue
	# 	FROM(SELECT *,(MIN(endDate, ?) - MAX(startDate, ?)) as availTime
	# 	FROM Queues
	# 	WHERE availTime>0)'''
	# # print query
	# curs.execute(query, [end_date, start_date])
	# cluster_total_avail_time = float(curs.fetchall()[0][0]) * 24.0
	cluster_total_avail_time = get_queue_avail_time(database, "total", 24, start_date, end_date)
	days = []
	x = []
	for d in range(start_date, end_date, 86400):
		start = dt.fromtimestamp(d, tz)
		end = dt.fromtimestamp(d + 86400, tz)
		days.append([start, end])
		x.append(start)
	# print(days)
	query = '''
	SELECT jobId,
	Group_Member.userName, 
	startTime, 
	endTime, 
	numAllocSlots, 
	(MIN(endTime, {}) - MAX(startTime, {})) as execWTime
	FROM lsfjobs 
	INNER JOIN Group_Member ON (lsfjobs.userName=Group_Member.userName) AND (groupName="{}")
	WHERE (execWTime > 0)
	'''.format(end_date, start_date, selected_group)
	# print(query)
	cnx = database
	df_groups = pd.read_sql_query(query, cnx)
	# print(df_groups)
	# List of users
	users = df_groups['userName'].unique()
	# print(users)

	data = []
	data_cum = []
	data_pie = []
	for u in users:
		y = []
		y_cum = []
		df = df_groups.loc[(df_groups['userName'] == u)]
		# print(u)
		x = []
		for [start, end] in days:
			x.append(start)
			# x.append(start.strftime("%d %b, %Y"))
			# print('user = {}, start_date = {}, end_date = {}'.format(u, start, end))
			df['start_period'] = int(start.timestamp())
			df['end_period'] = int(end.timestamp())
			df['coreHours'] = df.apply(calculate_core_hours, axis=1)
			# print(df)
			core_hours = df['coreHours'].loc[df.coreHours > 0].sum()
			if len(y_cum) == 0:
				prev = 0
			else:
				prev = y_cum[-1]
			y_cum.append(core_hours+prev)
			y.append(core_hours)
			# df['coreHours']=min(df['endTime'], df['end_period']) - max(df['startTime'], df['start_period'])
		data.append(go.Scatter(x=x, y=y, name=u))
		data_cum.append(go.Scatter(x=x, y=y_cum, fill='tonexty', name=u, stackgroup='one'))
		data_pie.append(y_cum[-1])

	area = html.Div(  # Beginning division of area
		children=[
			dcc.Graph(
				id='area',
				figure=go.Figure(
					data=data,
					layout=go.Layout(
						title='<b>Users utilization Timeline</b>',
						legend=go.layout.Legend(traceorder='normal'),
						yaxis=go.layout.YAxis(
							title=go.layout.yaxis.Title(
								text="Core Hours",
							)
						)
					)
				)
			)
		],
		# style={'width': '80%', 'padding-left': '10%', 'padding-right': '10%'}
	)

	area_cum = html.Div(  # Beginning division of area
		children=[
			dcc.Graph(
				id='area_cum',
				figure=go.Figure(
					data=data_cum,
					layout=go.Layout(
						title='<b>Cumulative Users utilization Timeline</b>',
						legend=go.layout.Legend(traceorder='normal'),
						yaxis=go.layout.YAxis(
							title=go.layout.yaxis.Title(
								text="Core Hours",
							)
						)
					)
				)
			)
		],
		# style={'width': '80%', 'padding-left': '10%', 'padding-right': '10%'}
	)

	pie_group = dcc.Graph(
		id='pie_1',
		figure=go.Figure(
			data=[go.Pie(labels=users, values=data_pie, sort=False)],
			layout=go.Layout(
				title='<b>Users utilization in the Group</b>',
				height=500
			)
		)

	)
	pie_util = dcc.Graph(
		id='pie_2',
		figure=go.Figure(
			data=[go.Pie(
				labels=['Used', 'Unused'],
				values=[sum(data_pie), ((cluster_total_avail_time/3600.0))-sum(data_pie)],
				sort=False)],
			layout=go.Layout(
				title='<b>Group utilization in the Cluster</b>',
				height=500
			)
		)
	)

	pies = html.Div([
		html.Div([
			pie_group
		], className="six columns"),

		html.Div([
			pie_util
		], className="six columns"),
	], className="row")
	return area, area_cum, pies


def create_group_ranking_charts(database, cluster, queue_list, s_date, e_date):
	# calculate totalCores

	print(cluster)
	# print(database)
	print(s_date)
	print(e_date)
	start_date = int(s_date.timestamp())
	end_date = int(e_date.timestamp())
	total_avail_time = 0
	for q in cluster.queues:
		if q['name'] in queue_list:
			total_avail_time = total_avail_time + get_queue_avail_time(database, q['name'], q['coresPerNode'], start_date, end_date)
	expanded_queue_list = queue_list.copy()
	if 'general' in expanded_queue_list:
		expanded_queue_list.extend(['interactive', 'normal'])
	if 'training' in expanded_queue_list:
		expanded_queue_list.extend(['test'])
	expanded_queue_list = ('queue="'+s+'"' for s in expanded_queue_list)
	queue_query = ' or '.join(expanded_queue_list)
	print(queue_query)
	# Collect information from the database
	query = '''
	SELECT 
		groupName,
		PI, 
		SUM(execWTime * numAllocSlots)/3600.0 as coreHours, 
		(SUM(execWTime * numAllocSlots))/({}) as percentage
	FROM(
		SELECT 
			groupName,
			queue,
			userName,
			MIN(endTime, {}) - MAX(startTime, {}) as execWTime, 
			numAllocSlots, 
			submitTime, 
			PI
		FROM lsfjobs 
		INNER JOIN Group_Member USING(userName)
		INNER JOIN Groups USING(groupName)
		WHERE (dateIn <= submitTime) and (dateOut >= submitTime) and (execWTime > 0) and ({})
	)
	GROUP BY groupName
	ORDER BY coreHours DESC
	'''.format(float(total_avail_time), end_date, start_date, queue_query)
	# print(query)
	cnx = database
	df_groups_rank = pd.read_sql_query(query, cnx)
	df_groups_rank['cumsum'] = df_groups_rank.loc[::-1, 'percentage'].cumsum()[::-1]

	total_utilization = df_groups_rank['coreHours'].sum()
	# total_available = ((end_date - start_date) * total_cores/3600)
	idle_utilization = (total_avail_time/3600) - total_utilization
	rest_group_utilization = df_groups_rank['coreHours'].loc[df_groups_rank['cumsum'] < 0.05].sum()
	print(total_avail_time)
	print(total_utilization)
	print(idle_utilization)
	print(rest_group_utilization)
	print(df_groups_rank['coreHours'])
	info_table = html.Div(  # Beginning division of table
		children=[
			html.H5(children='Ranking of Utilization (groups un pink add less than 5% of the total utilization)'),
			dash_table.DataTable(
				columns=[
					{"name": 'Group Name', "id": 'groupName', 'type': 'text'},
					{"name": 'Principal Investigator', "id": 'PI', 'type': 'text'},
					{"name": 'Core Hours', "id": 'coreHours', 'type': 'numeric', 'format': \
						FormatTemplate.Format(precision=3, scheme=FormatTemplate.Scheme.fixed)},
					{"name": 'Percentage', "id": 'percentage',  'type': 'numeric', 'format': FormatTemplate.percentage(3)},
					{"name": 'Cumsum', "id": 'cumsum', 'type': 'numeric', 'hidden': 'true'}
				],
				data=df_groups_rank.to_dict('records'),
				style_cell={'textAlign': 'left'},
				style_cell_conditional=[
					{
						'if': {'column_id': c},
						'textAlign': 'right'
					} for c in ['coreHours', 'percentage']
				],
				style_data_conditional=[
					{
						'if': {
							'filter_query': '{cumsum} < 0.05',
						},
						'backgroundColor': '{}'.format(rest_color)
					}
				]
			)
		],
		style={'width': '80%', 'padding-left': '10%', 'padding-right': '10%'}
	)  # End division of table

	excel_filename = 'group_ranking_sheet_{}.xlsx'.format(dt.timestamp(dt.now()))
	excel_relative_filename = os.path.join(
		'downloads',
		excel_filename
	)
	excel_absolute_filename = os.path.join(os.getcwd(), excel_relative_filename)
	# Create a Pandas Excel writer using XlsxWriter as the engine.
	writer = pd.ExcelWriter(excel_absolute_filename, engine='xlsxwriter')
	excel_title = '{} - Groups Utilization from {} to {} - Based on jobs submitted to {}. Total utilization = {:.2%}'. \
		format(
			cluster.clusterName,
			s_date.strftime('%Y-%m-%d %H:%M:%S'),
			(e_date - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
			', '.join(queue_list) + 'queue(s)',
			df_groups_rank['percentage'].sum()
		)

	# Convert the dataframe to an XlsxWriter Excel object.
	df_groups_rank[['groupName', 'PI', 'coreHours', 'percentage', 'cumsum']].to_excel(writer, sheet_name='Sheet1', startrow=2, index=False, header=False)

	# Get the xlsxwriter workbook and worksheet objects.
	workbook = writer.book
	worksheet = writer.sheets['Sheet1']
	worksheet.merge_range('A1:Z1', excel_title)
	# worksheet.write_string(0, 0, excel_title)

	# here we create a format object for header.
	header_format_object = workbook.add_format({
		'bold': True
	})
	worksheet.write(1, 0, 'Group Name', header_format_object)
	worksheet.write(1, 1, 'Principal Investigator', header_format_object)
	worksheet.write(1, 2, 'Core Hours', header_format_object)
	worksheet.write(1, 3, 'Percentage', header_format_object)
	worksheet.write(1, 4, 'Cumulative Percentage', header_format_object)
	# Add some cell formats.
	format1 = workbook.add_format({'num_format': '#,##0.00'})
	format2 = workbook.add_format({'num_format': '0.000%'})
	format3 = workbook.add_format({'bg_color': '#FFF0F5'})

	# Note: It isn't possible to format any cells that already have a format such
	# as the index or headers or any cells that contain dates or datetimes.
	worksheet.set_column('A:A', 30)
	worksheet.set_column('B:B', 30)
	# Set the column width and format.
	worksheet.set_column('C:C', 15, format1)

	# Set the format but not the column width.
	worksheet.set_column('D:D', 15, format2)
	worksheet.set_column('E:E', 20, format2, {'hidden': True})
	worksheet.conditional_format("A3:E$%d" % (len(df_groups_rank.index)+2),
		{
			"type": "formula",
			"criteria": '= INDIRECT("E" & ROW()) <= 0.05',
			"format": format3
		}
	)

	# Close the Pandas Excel writer and output the Excel file.
	writer.save()

	df_aux = df_groups_rank[['groupName', 'coreHours']].loc[df_groups_rank['cumsum'] >= 0.05]
	color = []
	for ii in range(len(df_aux.index)):
		c = color_palette[ii % len(color_palette)]
		color.append(c)
		print([c, ii])
	# https://www.w3schools.com/cssref/css_colors.asp

	color.append(idle_color)
	color.append(rest_color)
	df_groups_pie = df_aux.append(pd.DataFrame({'groupName': ['IDLE', 'Rest of the groups'], 'coreHours':\
		[idle_utilization, rest_group_utilization]}), ignore_index=True)
	df_groups_pie['colors'] = color
	print(df_groups_pie)

	#pie_title = '<b>Groups utilization - Total utilization = {:.2%}</b>'.format(df_groups_rank['percentage'].sum())
	pie_title = '<b>{} - Groups Utilization from {} to {}</b><br>Based on jobs submitted to {}.<br><b>Total utilization = {:.2%}</b>'.\
		format(
			cluster.clusterName,
			s_date.strftime('%Y-%m-%d %H:%M:%S'),
			(e_date-timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
			'<i>'+', '.join(queue_list)+'</i> queue(s)',
			df_groups_rank['percentage'].sum()
		)
	print(pie_title)
	pie_group = dcc.Graph(
		config={
			'toImageButtonOptions': {
				'format': 'svg',
				'filename': 'group_ranking_chart',
				'height': 700,
				'width': 700,
				'scale': 1
			}
		},
		id='groups_pie',
		figure=go.Figure(
			data=[go.Pie(labels=df_groups_pie['groupName'], values=df_groups_pie['coreHours'],\
				marker=dict(colors=color), sort=False, hole=0.3)],
			layout=go.Layout(
				title=pie_title,
				height=700
			)
		)

	)
	# print(df_groups_pie)
	# print(df_groups_rank)
	return info_table, pie_group, '/{}'.format(excel_relative_filename)


def get_group_parent(row):
	parent = 'MI Cluster'
	if row['cumsum']<0.05:
		parent = 'Rest of the groups'
	return parent

def get_user_ids(row):
	return str(row['userName'] + '-' + row['groupName'])



def create_group_sunburst(database, cluster, queue_list, s_date, e_date):

	# calculate totalCores

	print(cluster)
	# print(database)
	print(s_date)
	print(e_date)
	start_date = int(s_date.timestamp())
	end_date = int(e_date.timestamp())
	total_avail_time = 0
	for q in cluster.queues:
		if q['name'] in queue_list:
			total_avail_time = total_avail_time + get_queue_avail_time(database, q['name'], q['coresPerNode'],
																	   start_date, end_date)
	expanded_queue_list = queue_list.copy()
	if 'general' in expanded_queue_list:
		expanded_queue_list.extend(['interactive', 'normal'])
	if 'training' in expanded_queue_list:
		expanded_queue_list.extend(['test'])
	expanded_queue_list = ('queue="'+s+'"' for s in expanded_queue_list)
	queue_query = ' or '.join(expanded_queue_list)
	print(queue_query)
	# Collect information from the database
	query = '''
	SELECT 
		groupName,
		PI, 
		SUM(execWTime * numAllocSlots) as coreHours, 
		(SUM(execWTime * numAllocSlots))/({}) as percentage
	FROM(
		SELECT 
			groupName,
			queue,
			userName,
			MIN(endTime, {}) - MAX(startTime, {}) as execWTime, 
			numAllocSlots, 
			submitTime, 
			PI
		FROM lsfjobs 
		INNER JOIN Group_Member USING(userName)
		INNER JOIN Groups USING(groupName)
		WHERE (dateIn <= submitTime) and (dateOut >= submitTime) and (execWTime > 0) and ({})
	)
	GROUP BY groupName
	ORDER BY coreHours DESC
	'''.format(float(total_avail_time), end_date, start_date, queue_query)
	# print(query)
	cnx = database
	df_groups_rank = pd.read_sql_query(query, cnx)
	df_groups_rank['cumsum'] = df_groups_rank.loc[::-1, 'percentage'].cumsum()[::-1]

	total_utilization = df_groups_rank['coreHours'].sum()
	# total_available = ((end_date - start_date) * total_cores)
	idle_utilization = (total_avail_time - total_utilization)
	rest_group_utilization = df_groups_rank['coreHours'].loc[df_groups_rank['cumsum'] < 0.05].sum()
	print(total_avail_time)
	print(total_utilization)
	print(idle_utilization)
	print(rest_group_utilization)
	# print(df_groups_rank['coreHours'])

	df_groups_rank['parent'] = df_groups_rank.apply(get_group_parent, axis=1)
	df_aux = df_groups_rank[['groupName', 'coreHours']].loc[df_groups_rank['cumsum'] >= 0.05]
	color = []
	for ii in range(len(df_aux.index)):
		c = color_palette[ii % len(color_palette)]
		color.append(c)
		print([c, ii])
	# https://www.w3schools.com/cssref/css_colors.asp

	# Sunburst cannot be plotted in specific order. We need to reorder the color list so Idle and Rest get always the same colors
	df_aux['colors'] = color
	df_aux = df_aux.append(pd.DataFrame({'groupName': ['IDLE', 'Rest of the groups'], 'coreHours':\
		[idle_utilization, rest_group_utilization], 'colors': [idle_color, rest_color]}), ignore_index=True)

	df_aux = df_aux.sort_values(by=['coreHours'], ascending=False)
	print(df_aux)
	color = df_aux['colors'].tolist()
	# End of color reordering

	df_aux = df_aux.append(pd.DataFrame({'groupName': ['MI Cluster', 'IDLE', 'Rest of the groups'], 'coreHours':\
		[total_avail_time, idle_utilization, rest_group_utilization], 'parent': ['', 'MI Cluster', 'MI Cluster']}), ignore_index=True)

	df_groups_rank = df_groups_rank.append(pd.DataFrame({'groupName': ['MI Cluster', 'IDLE', 'Rest of the groups'], 'coreHours':\
		[total_avail_time, idle_utilization, rest_group_utilization], 'parent': ['', 'MI Cluster', 'MI Cluster']}), ignore_index=True)

	ids = df_groups_rank['groupName'].tolist()
	labels = df_groups_rank['groupName'].tolist()
	values = df_groups_rank['coreHours'].tolist()
	parents = df_groups_rank['parent'].tolist()

	print(df_groups_rank)

	query = '''
	SELECT 
		userName,
		groupName,
		PI, 
		SUM(execWTime * numAllocSlots) as coreHours, 
		(SUM(execWTime * numAllocSlots))/({}) as percentage
	FROM(
		SELECT 
			groupName,
			queue,
			userName,
			MIN(endTime, {}) - MAX(startTime, {}) as execWTime, 
			numAllocSlots, 
			submitTime, 
			PI
		FROM lsfjobs 
		INNER JOIN Group_Member USING(userName)
		INNER JOIN Groups USING(groupName)
		WHERE (dateIn <= submitTime) and (dateOut >= submitTime) and (execWTime > 0) and ({})
	)
	GROUP BY userName, groupName
	ORDER BY groupName ASC, coreHours DESC
	'''.format(float(total_avail_time), end_date, start_date, queue_query)
	# print(query)
	# cnx = sqlite3.connect(database)
	df_users = pd.read_sql_query(query, cnx)
	df_users['ids'] = df_users.apply(get_user_ids, axis=1)
	# print(df_users)
	ids.extend(df_users['ids'])
	labels.extend(df_users['userName'])
	values.extend(df_users['coreHours'])
	parents.extend(df_users['groupName'])

	#calculate percentage
	df_all=pd.DataFrame({'ids': ids, 'labels': labels, 'parents': parents, 'values': values})

	# print(df_all)
	percentages = []
	for index, row in df_all.iterrows():
		if row['parents']=='Rest of the groups':
			percentages.append('{0:.2%}'.format(float(row['values']) / total_avail_time))
		else:
			idx = df_all.loc[df_all['ids'] == row['parents']]
			if len(idx.index) == 0:
				percentages.append('{0:.2%}'.format(total_utilization/total_avail_time))
			else:
				percentages.append('{0:.2%}'.format(float(row['values']) / float(idx['values'])))

	print(percentages)
	sunburst_title = '<b>{} - Groups and Users Utilization from {} to {}</b><br>Based on jobs submitted to {}.<br><i>Percentage of utilization of the Users are relative to their Groups</i>'. \
		format(
			cluster.clusterName,
			s_date.strftime('%Y-%m-%d %H:%M:%S'),
			(e_date - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
			'<i>' + ', '.join(queue_list) + '</i> queue(s)',
		)
	sunburst = dcc.Graph(
		id='sunburst',
		config={
			'toImageButtonOptions': {
				'format': 'svg',
				'filename': 'sunburst',
				'height': 700,
				'width': 700,
				'scale': 1
			}
		},
		figure=go.Figure(
			data=[go.Sunburst(
				hoverinfo='label+text',
				text=percentages,
				ids=ids,
				labels=labels,
				parents=parents,
				values=values,
				branchvalues="total",
				outsidetextfont={"size": 20, "color": "#377eb8"},
				leaf={"opacity": 0.4},
				marker={"line": {"width": 2}}
			)],
			layout=go.Layout(
				#margin=go.layout.Margin(t=0, l=0, r=0, b=0),
				sunburstcolorway=color,
				# sunburstcolorway=["#17BECF", "#C6AEDC", "#A74E00"],
				title=sunburst_title,
				height=1000
			)
		)
	)
	# print(df_groups_pie)
	# print(df_groups_rank)
	return sunburst

def create_cluster_utilization_bars(database, cluster, s_date, e_date):
	# calculate totalCores
	total_cores = 0
	q_cores = []
	queue_list = []
	for q in cluster.queues:
		queue_list.append(q['name'])
		q_cores.append(q['coresPerNode'])
	print(total_cores)
	print(cluster)
	# print(database)
	print(s_date)
	print(e_date)
	start_date = int(s_date.timestamp())
	end_date = int(e_date.timestamp())
	# create a list of dates
	date_1 = s_date.replace(day=1)
	date_2 = e_date.replace(day=1)
	months = []
	months_str = []
	while date_1 < date_2:
		month = date_1.month
		year = date_1.year
		next_month = month + 1 if month != 12 else 1
		next_year = year + 1 if next_month == 1 else year
		date_aux = date_1.replace(month=next_month, year=next_year)
		months.append([date_1, date_aux])
		months_str.append(date_1.strftime('%b%y'))
		date_1 = date_aux
	print(months)
	cnx = database
	curs = cnx.cursor()
	curs.execute('''DROP TABLE if exists queueinfo''')
	cnx.commit()
	df_queues = pd.DataFrame(columns=queue_list, index=months_str)
	print(df_queues)
	df_cluster = pd.DataFrame(columns=queue_list, index=months_str)
	print(df_cluster)
	for d in months:
		date_str = d[0].strftime('%b%y')
		start = int(d[0].timestamp())
		end = int(d[1].timestamp())
		# cluster_total_avail_time = total_cores * (float(end) - float(start))

		# query = '''SELECT total(availTime*(total)) as availTimeQueue
		# 	FROM(SELECT *,(MIN(endDate, ?) - MAX(startDate, ?)) as availTime
		# 	FROM Queues
		# 	WHERE availTime>0)'''
		# # print query
		# curs.execute(query, [end, start])
		# cluster_total_avail_time = float(curs.fetchall()[0][0]) * 24.0
		cluster_total_avail_time = get_queue_avail_time(database, "total", 24, start, end)

		query = '''CREATE TABLE queueinfo AS 
			SELECT queue, numAllocSlots, execWTime 
			FROM(SELECT queue, numAllocSlots, startTime, endTime, (MIN(endTime, ?) - MAX(startTime, ?)) as execWTime 
			FROM lsfjobs 
			WHERE (execWTime>0 and startTime!=0))'''
		curs.execute(query, [end, start])
		for q, q_c in zip(queue_list, q_cores):
			# queue_total_avail_time = q_c * (float(end) - float(start))

			# query = '''SELECT total(availTime*(%s)) as availTimeQueue
			# 	FROM(SELECT *,(MIN(endDate, ?) - MAX(startDate, ?)) as availTime
			# 	FROM Queues
			# 	WHERE availTime>0)''' % q
			# # print query
			# curs.execute(query, [end, start])
			# queue_total_avail_time = float(curs.fetchall()[0][0]) * q_c
			queue_total_avail_time = get_queue_avail_time(database, q, q_c, start, end)
			query = '''SELECT total(execWTime * numAllocSlots) AS "Total used time" 
					FROM queueinfo
					WHERE (queue="{}")'''.format(q)
			if q == 'general':
				query = query[:-1] + ' or queue="normal" or queue="interactive"' + query[-1]
			if q == 'training':
				query = query[:-1] + ' or queue="test"' + query[-1]
			# print(query)
			df_q = pd.read_sql_query(query, cnx)
			# print(df_q["Total used time"][0])
			try:
				df_cluster[q][date_str] = df_q["Total used time"][0]/cluster_total_avail_time
			except:
				df_cluster[q][date_str] = 0.0
			try:
				df_queues[q][date_str] = df_q["Total used time"][0]/queue_total_avail_time
			except:
				df_queues[q][date_str] = 0.0
		curs.execute('''DROP TABLE queueinfo''')
	# cnx.close()
	print(df_cluster)
	print(df_queues)
	utilization_title = '<b>{} - Cluster Utilization from {} to {}</b><br>Based on jobs submitted to {}.<br><i>Percentage of utilization of the Queues is relative to the entire Cluster</i>'. \
		format(
			cluster.clusterName,
			s_date.strftime('%Y-%m-%d %H:%M:%S'),
			(e_date - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
			'<i>' + ', '.join(queue_list) + '</i> queue(s)'
		)
	print(utilization_title)
	data = []
	for q in queue_list:
		trace = go.Bar(
			x=months_str,
			y=df_cluster[q].tolist(),
			name=q
		)
		data.append(trace)
	utilization = dcc.Graph(
		id='bar_cluster_utilization',
		config={
			'toImageButtonOptions': {
				'format': 'svg',
				'filename': 'cluster_utilization',
				'scale': 1
			}
		},
		figure=go.Figure(
			data=data,
			layout=go.Layout(
				title=utilization_title,
				height=800,
				yaxis=dict(tickformat=".2%", range=[0, 1]),
				barmode='stack'
			)
		)
	)

	queues_utilization_title = '<b>{} - Cluster Utilization from {} to {}</b><br>Based on jobs submitted to {}.<br><i>Percentage of utilization of the Queues is relative to the Queue itself</i>'. \
		format(
		cluster.clusterName,
		s_date.strftime('%Y-%m-%d %H:%M:%S'),
		(e_date - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
		'<i>' + ', '.join(queue_list) + '</i> queue(s)'
	)
	print(queues_utilization_title)
	data = []
	for q in queue_list:
		trace = go.Bar(
			x=months_str,
			y=df_queues[q].tolist(),
			name=q
		)
		data.append(trace)
	queues_utilization = dcc.Graph(
		id='bar_queues_utilization',
		config={
			'toImageButtonOptions': {
				'format': 'svg',
				'filename': 'cluster_utilization',
				'scale': 1
			}
		},
		figure=go.Figure(
			data=data,
			layout=go.Layout(
				title=queues_utilization_title,
				height=800,
				yaxis=dict(tickformat=".2%", range=[0, 1]),
				# barmode='stack'
			)
		)
	)

	return utilization, queues_utilization


def create_nodes_occupancy_bars(database, cluster, s_date, e_date):
	nodes_file = cluster.nodes
	df_nodes = pd.read_json(nodes_file).transpose()



	# calculate totalCores
	total_cores = 0
	q_cores = []
	q_nodes = []
	queue_list = []
	for q in cluster.queues:
		total_cores = total_cores+(q['coresPerNode']*q['nNodes'])
		queue_list.append(q['name'])
		q_cores.append(q['coresPerNode']*q['nNodes'])
		q_nodes.append(q['nNodes'])
	print(total_cores)
	print(cluster)
	# print(database)
	print(s_date)
	print(e_date)
	print(df_nodes)
	start_date = int(s_date.timestamp())
	end_date = int(e_date.timestamp())
	# create a list of dates

	cnx = database
	curs = cnx.cursor()
	curs.execute('''DROP TABLE if exists nodesinfo''')
	query = '''CREATE TABLE nodesinfo AS 
				SELECT allocSlotsStr, execWTime 
				FROM(SELECT allocSlotsStr, (MIN(endTime, ?) - MAX(startTime, ?)) as execWTime 
				FROM lsfjobs 
				WHERE (execWTime>0 and startTime!=0))'''
	curs.execute(query, [end_date, start_date])
	for node in df_nodes.index.values:
		print(node)
		df_nodes['availT'][node] = df_nodes['ncores'][node] * (float(end_date) - float(start_date))
		query = '''
				SELECT execWTime, allocSlotsStr
				FROM nodesinfo 
				WHERE (allocSlotsStr LIKE "{}")'''.format('%'+node+'%')
		df_n = pd.read_sql_query(query, cnx)
		df_nodes['usedT'][node] = 0.0
		df_nodes['njobs'][node] = len(df_n.index)
		for idx, j in df_n.iterrows():
			exec_time = float(j['execWTime'])
			all_cores = j['allocSlotsStr'].split()
			cores = all_cores.count(node)
			df_nodes['usedT'][node] += exec_time*cores
		df_nodes['occupation'][node] = float(df_nodes['usedT'][node])/float(df_nodes['availT'][node])

	curs.execute('''DROP TABLE nodesinfo''')
	print(df_nodes)
	# cnx.close()

	nodes_occupation_title = '<b>{} - Nodes occupation from {} to {}</b>'. \
		format(
			cluster.clusterName,
			s_date.strftime('%Y-%m-%d %H:%M:%S'),
			(e_date - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')
		)
	print(nodes_occupation_title)
	data = []
	# colors
	color = []
	text = []
	for q, c in zip(queue_list, color_palette[0:len(queue_list)]):
		for node in df_nodes.index.values:
			if df_nodes['queue'][node] == q:
				color.append(c)
				text.append(
					"Queue: {}<br>Jobs: {}<br>coreHours: {:.2f}".format(df_nodes['queue'][node], df_nodes['njobs'][node],
																		df_nodes['usedT'][node] / 3600))



	trace = go.Bar(
		x=df_nodes.index.values,
		y=df_nodes['occupation'],
		marker=dict(color=color),
		text=text
	)
	data.append(trace)
	nodes_occupation = dcc.Graph(
		id='bar_nodes_occupation',
		config={
			'toImageButtonOptions': {
				'format': 'svg',
				'filename': 'nodes_occupation',
				'scale': 1
			}
		},
		figure=go.Figure(
			data=data,
			layout=go.Layout(
				title=nodes_occupation_title,
				height=800,
				yaxis=dict(tickformat=".2%", range=[0, 1]),
				# barmode='stack'
			)
		)
	)
	return nodes_occupation

def create_node_counting_area(database, cluster, s_date, e_date):
	print("hello")


def initial_month(months_back):
	date = dt.now()
	m = date.month - months_back
	y = date.year
	if m < 1:
		m = 12 + m
		y = y - 1
	date = date.replace(month=m, year=y)
	print(date)
	return date


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


navBar = html.Nav([
	html.Div(id='selected_cluster', children=selected_cluster, style={'display': 'none'}),
	html.Div(
		html.H1(children=selected_cluster + ' Cluster Statistics'),
		style={'display': 'inline-block', 'width': '20%'}
	)]
)

groupStatsSubmit = html.Div([

		html.H5(children='Select period: '),

		dcc.DatePickerRange(
			id='group-stats-date-picker-range',
			# min_date_allowed=dt(1995, 8, 5),
			# max_date_allowed=dt(2020, 9, 19),
			initial_visible_month=initial_month(4),
			day_size=50,
			month_format='MMMM YYYY',
			end_date_placeholder_text='End date',
			start_date_placeholder_text='Start date',
			number_of_months_shown=5,
		),
		html.H5(children='Select a group: '),
		# html.Div(id='group_stats_dropdown', children=[html.P(children='Select a cluster first!')], value=None),
		dcc.Dropdown(
			id='group_stats_dropdown',
			disabled='True',
			placeholder="Select a group",
			value=None
		),
		html.Button('Submit', id='group_stats_submit_button'),
		html.Div(id='group_stats_container_submit_button')
	],
	style={'display': 'inline-block', 'width': '20%'}
)

groupRankingSubmit = html.Div([

		html.H5(children='Select period: '),

		dcc.DatePickerRange(
			id='group-ranking-date-picker-range',
			# min_date_allowed=dt(1995, 8, 5),
			# max_date_allowed=dt(2020, 9, 19),
			initial_visible_month=initial_month(4),
			day_size=50,
			month_format='MMMM YYYY',
			end_date_placeholder_text='End date',
			start_date_placeholder_text='Start date',
			number_of_months_shown=5,
		),
		html.H5(children='Select a queue: '),
		# html.Div(id='group_stats_dropdown', children=[html.P(children='Select a cluster first!')], value=None),
		dcc.Dropdown(
			id='group_ranking_queue_dropdown',
			multi=True,
			disabled='True',
			placeholder="Select a queue",
			value=None
		),
		html.Button('Submit', id='group_ranking_submit_button'),
		html.Div(id='group_ranking_container_submit_button')
	],
	style={'display': 'inline-block', 'width': '20%'}
)

groupSunburstSubmit = html.Div([

		html.H5(children='Select period: '),

		dcc.DatePickerRange(
			id='group-sunburst-date-picker-range',
			# min_date_allowed=dt(1995, 8, 5),
			# max_date_allowed=dt(2020, 9, 19),
			initial_visible_month=initial_month(4),
			day_size=50,
			month_format='MMMM YYYY',
			end_date_placeholder_text='End date',
			start_date_placeholder_text='Start date',
			number_of_months_shown=5,
		),
		html.H5(children='Select a queue: '),
		# html.Div(id='group_stats_dropdown', children=[html.P(children='Select a cluster first!')], value=None),
		dcc.Dropdown(
			id='group_sunburst_queue_dropdown',
			multi=True,
			disabled='True',
			placeholder="Select a queue",
			value=None
		),
		html.Button('Submit', id='group_sunburst_submit_button'),
		html.Div(id='group_sunburst_container_submit_button')
	],
	style={'display': 'inline-block', 'width': '20%'}
)

clusterUtilizationSubmit = html.Div([

		html.H5(children='Select period: '),

		dcc.DatePickerRange(
			id='cluster-utilization-date-picker-range',
			# min_date_allowed=dt(1995, 8, 5),
			# max_date_allowed=dt(2020, 9, 19),
			initial_visible_month=initial_month(4),
			day_size=50,
			month_format='MMMM YYYY',
			end_date_placeholder_text='End date',
			start_date_placeholder_text='Start date',
			number_of_months_shown=5,
		),
		html.Button('Submit', id='cluster_utilization_submit_button'),
		html.Div(id='cluster_utilization_container_submit_button')
	],
	style={'display': 'inline-block', 'width': '20%'}
)

nodesUtilizationSubmit = html.Div([

		html.H5(children='Select period: '),

		dcc.DatePickerRange(
			id='nodes-occupancy-date-picker-range',
			# min_date_allowed=dt(1995, 8, 5),
			# max_date_allowed=dt(2020, 9, 19),
			initial_visible_month=initial_month(4),
			day_size=50,
			month_format='MMMM YYYY',
			end_date_placeholder_text='End date',
			start_date_placeholder_text='Start date',
			number_of_months_shown=5,
		),
		html.Button('Submit', id='nodes_occupancy_submit_button'),
		html.Div(id='nodes_occupancy_container_submit_button')
	],
	style={'display': 'inline-block', 'width': '20%'}
)

nodeCountingSubmit = html.Div([

		html.H5(children='Select period: '),

		dcc.DatePickerRange(
			id='node-counting-date-picker-range',
			# min_date_allowed=dt(1995, 8, 5),
			# max_date_allowed=dt(2020, 9, 19),
			initial_visible_month=initial_month(4),
			day_size=50,
			month_format='MMMM YYYY',
			end_date_placeholder_text='End date',
			start_date_placeholder_text='Start date',
			number_of_months_shown=5,
		),
		html.Button('Submit', id='node_counting_submit_button'),
		html.Div(id='node_counting_container_submit_button')
	],
	style={'display': 'inline-block', 'width': '20%'}
)

DB = None

app.layout = html.Div(
	children=[
		# Hidden div inside the app that stores the intermediate value
		html.Div(id='intermediate-value', style={'display': 'none'}),
		navBar,
		dcc.Tabs(id="main_tabs", children=[
			dcc.Tab(label='Cluster', children=[
				html.Div([
					dcc.Tabs(
						id="cluster_tabs",
						vertical='True',
						style={'width': '20%'},
						parent_style={'width': '100%'},
						content_style={'width': '100%'},
						children=[
							dcc.Tab(
								label='Cluster Info',
								children=[
									html.Div([
										dcc.Loading(id="loading-cluster-info", children=[html.Div(id='cluster_info_table')], type="default"),
									])
								]
							),
							dcc.Tab(
								label='Cluster Utilization',
								children=[
									clusterUtilizationSubmit,
									html.Div([
										dcc.Loading(id="loading-cluster-utilization", children=[html.Div(id='cluster_utilization')], type="default")
									]),
									html.Div([
										dcc.Loading(id="loading-queues-utilization", children=[html.Div(id='queues_utilization')], type="default")
									])
								]
							),
							dcc.Tab(
								label='Nodes Occupancy',
								children=[
									nodesUtilizationSubmit,
									html.Div([
										dcc.Loading(id="loading-nodes-occupancy", children=[html.Div(id='nodes_occupancy')], type="default"),
									])
								]
							),
							dcc.Tab(
								label='Node Counting',
								children=[
									nodeCountingSubmit,
									html.Div([
										dcc.Loading(id="loading-node-counting",
													children=[html.Div(id='node_counting')], type="default"),
									])
								]
							),
						]
					)
				])
			]),  # End Tab Cluster
			dcc.Tab(label='Groups', children=[
				html.Div([
					dcc.Tabs(
						id="group_tabs",
						vertical='True',
						style={'width': '20%'},
						parent_style={'width': '100%'},
						content_style={'width': '100%'},
						children=[
							dcc.Tab(
								label='Add Group',
								children=[
									html.Div([])
								]),  # End Vertical Tab Add Group
							dcc.Tab(
								label='Group List',
								children=[
									html.Div([
										dcc.Loading(id="loading-list-group", children=[html.Div(id='group_list_table')], type="default"),
									])
								]),  # End Vertical Tab Add Group
							dcc.Tab(
								label='Group Stats',
								children=[
									html.Div(id='group-stats-intermediate-value', style={'display': 'none'}),
									groupStatsSubmit,
									html.Div(
										[
											dcc.Loading(id="group_stats_pies_loading",children=[html.Div(id='group_stats_pies')], type="default"),
										]
									),
									html.Div(
										[
											dcc.Loading(id="group_stats_gantt_loading", children=[html.Div(id='group_stats_gantt')], type="default"),
										],
										style={'display': 'none'}
									),
									html.Div(
										[
											dcc.Loading(id="group_stats_area_loading", children=[html.Div(id='group_stats_area')], type="default"),
										]
									),
									html.Div(
										[
											dcc.Loading(id="group_stats_area_cum_loading", children=[html.Div(id='group_stats_area_cum')], type="default"),
										]
									)
								]
							),  # End Vertical Tab Groups Stats
							dcc.Tab(
								label='Groups Ranking',
								children=[
									groupRankingSubmit,
									html.Div(
										[
											dcc.Loading(id="group_ranking_pie_loading", children=[
												html.Div(id='group_ranking_pie'),
											], type="default"),
										]
									),
									html.Div(
										[
											dcc.Loading(id="group_ranking_table_loading", children=[
												html.Div(id='group_ranking_table'),
												html.A(
													html.Button('Download table', hidden=True),
													id='download_table',
													download='group_ranking_sheet.xlsx'
												)
											], type="default"),
										]
									)
								]
							),  # End Vertical Tab Group Ranking
							dcc.Tab(
								label='Groups and Users',
								children=[
									groupSunburstSubmit,
									html.Div(
										[
											dcc.Loading(id="group_sunburst_loading", children=[
												html.Div(id='group_sunburst'),
											], type="default"),
										]
									),
									# html.Div(
									# 	[
									# 		dcc.Graph(
									# 			id='test',
									# 			config={
									# 				'toImageButtonOptions': {
									# 					'format': 'svg',
									# 					'filename': 'sunburst',
									# 					'height': 700,
									# 					'width': 700,
									# 					'scale': 1
									# 				}
									# 			},
									# 			figure=go.Figure(
									# 				data=[go.Sunburst(
									# 					ids=[
									# 						"North America", "Europe", "Australia", "North America - Football", "Soccer",
									# 						"North America - Rugby", "Europe - Football", "Rugby",
									# 						"Europe - American Football","Australia - Football", "Association",
									# 						"Australian Rules", "Autstralia - American Football", "Australia - Rugby",
									# 						"Rugby League", "Rugby Union"
									# 					],
									# 					labels=[
									# 						"North<br>America", "Europe", "Australia", "Football", "Soccer", "Rugby",
									# 						"Football", "Rugby", "American<br>Football", "Football", "Association",
									# 						"Australian<br>Rules", "American<br>Football", "Rugby", "Rugby<br>League",
									# 						"Rugby<br>Union"
									# 					],
									# 					parents=[
									# 						"", "", "", "North America", "North America", "North America", "Europe",
									# 						"Europe", "Europe","Australia", "Australia - Football", "Australia - Football",
									# 						"Australia - Football", "Australia - Football", "Australia - Rugby",
									# 						"Australia - Rugby"
									# 					],
									# 					outsidetextfont={"size": 20, "color": "#377eb8"},
									# 					leaf={"opacity": 0.4},
									# 					marker={"line": {"width": 2}}
									# 				)],
									# 				layout=go.Layout(
									# 					margin = go.layout.Margin(t=0, l=0, r=0, b=0),
									# 					sunburstcolorway=["#17BECF", "#C6AEDC", "#A74E00"],
									# 					height=700
									# 				)
									# 			)
									# 		)
									# 	]
									# )
								]
							),  # End Vertical Tab Group Ranking
						]
					)  # End Vertical Tabs
				])  # End Div Vertical tabs
			])  # End Tab Groups
		])  # End Horizontal Tabs (main_tabs)
	],
)


@app.callback(
	[Output(component_id='cluster_info_table', component_property='children'),
		Output(component_id='group_list_table', component_property='children'),
		Output(component_id='group_stats_dropdown', component_property='options'),
		Output(component_id='group_stats_dropdown', component_property='disabled'),
		Output(component_id='group_ranking_queue_dropdown', component_property='options'),
		Output(component_id='group_ranking_queue_dropdown', component_property='disabled'),
		Output(component_id='group_sunburst_queue_dropdown', component_property='options'),
		Output(component_id='group_sunburst_queue_dropdown', component_property='disabled'),],
	[Input(component_id='selected_cluster', component_property='children')]
)
def update_cluster_info_table_div(input_value):
	if input_value is not None:
		print('callback called!!!')
		cluster_table = create_info_table(input_value, df_config)
		print(df_config[input_value].database)
		group_list_table = create_group_list_table(MEM_DB)
		group_stats_dropdown = create_group_stats_dropdown(MEM_DB)
		group_ranking_queue_dropdown = create_group_ranking_queue_dropdown(df_config[input_value].queues)
		group_sunburst_queue_dropdown = create_group_ranking_queue_dropdown(df_config[input_value].queues)
		# mem_db = db.clone_db(df_config[input_value].database)
		return cluster_table, group_list_table, group_stats_dropdown, False, group_ranking_queue_dropdown, False,\
			   group_sunburst_queue_dropdown, False
	else:
		return None, None, 'Select a cluster first', True, 'Select a cluster first', True, 'Select a cluster first',\
			   True


@app.callback(
	[dash.dependencies.Output('group_stats_container_submit_button', component_property='children'),
		dash.dependencies.Output('group_stats_gantt', component_property='children'),
		dash.dependencies.Output('group_stats_area', component_property='children'),
		dash.dependencies.Output('group_stats_area_cum', component_property='children'),
		dash.dependencies.Output('group_stats_pies', component_property='children')],
	[dash.dependencies.Input('group_stats_submit_button', component_property='n_clicks')],
	[dash.dependencies.State('group-stats-date-picker-range', component_property='start_date'),
		dash.dependencies.State('group-stats-date-picker-range', component_property='end_date'),
		dash.dependencies.State('group_stats_dropdown', component_property='value'),
		dash.dependencies.State(component_id='selected_cluster', component_property='children')])
def update_output(n_clicks, start_date, end_date, selected_group, selected_cluster):
	if start_date is not None and end_date is not None and selected_group is not None and selected_cluster is not None:
		s_date = tz.localize(dt.strptime(start_date, '%Y-%m-%d'))
		e_date = tz.localize(dt.strptime(end_date, '%Y-%m-%d'))
		if e_date > s_date:
			group_stats_gantt = create_group_stats_gantt(MEM_DB, selected_group, s_date, e_date)
			[group_stats_area, group_stats_area_cum, pies] = create_group_stats_area(MEM_DB, df_config[selected_cluster], selected_group, s_date, e_date)

			return ('The selected cluster is {}. The selected group is "{}" and the period is from {} to {}'.format(
				selected_cluster,
				selected_group,
				s_date.timestamp(),
				e_date.timestamp()
				), group_stats_gantt,
				group_stats_area,
				group_stats_area_cum,
				pies
			)
	else:
		return None, None, None, None, None


@app.callback(
	[dash.dependencies.Output('group_ranking_container_submit_button', component_property='children'),
		dash.dependencies.Output('group_ranking_table', component_property='children'),
		dash.dependencies.Output('group_ranking_pie', component_property='children'),
		dash.dependencies.Output('download_table', component_property='href'),
		dash.dependencies.Output('download_table', component_property='hidden')],
	[dash.dependencies.Input('group_ranking_submit_button', component_property='n_clicks')],
	[dash.dependencies.State('group-ranking-date-picker-range', component_property='start_date'),
		dash.dependencies.State('group-ranking-date-picker-range', component_property='end_date'),
		dash.dependencies.State(component_id='selected_cluster', component_property='children'),
		dash.dependencies.State('group_ranking_queue_dropdown', component_property='value')])
def update_output(n_clicks, start_date, end_date, selected_cluster, queue_list):
	if start_date is not None and end_date is not None and selected_cluster is not None and queue_list is not None:
		s_date = tz.localize(dt.strptime(start_date, '%Y-%m-%d'))
		e_date = tz.localize(dt.strptime(end_date, '%Y-%m-%d'))
		print(type(queue_list))
		print(queue_list)
		print((len(queue_list) > 0))
		group_ranking_table = None
		group_ranking_pie = None
		excel_path = None

		if (e_date > s_date) and (len(queue_list) > 0):
			print(queue_list)
			[group_ranking_table, group_ranking_pie, excel_path] = create_group_ranking_charts(MEM_DB, df_config[selected_cluster], queue_list, s_date, e_date)

		return ('The selected cluster is {}. The period is from {} to {}'.format(
			selected_cluster,
			s_date.timestamp(),
			e_date.timestamp()
			),
			group_ranking_table,
			group_ranking_pie,
			excel_path,
			False
		)
	else:
		return None, None, None, None, True


@app.callback(
	[dash.dependencies.Output('group_sunburst_container_submit_button', component_property='children'),
		dash.dependencies.Output('group_sunburst', component_property='children')],
	[dash.dependencies.Input('group_sunburst_submit_button', component_property='n_clicks')],
	[dash.dependencies.State('group-sunburst-date-picker-range', component_property='start_date'),
		dash.dependencies.State('group-sunburst-date-picker-range', component_property='end_date'),
		dash.dependencies.State(component_id='selected_cluster', component_property='children'),
		dash.dependencies.State('group_sunburst_queue_dropdown', component_property='value')])
def update_sunburst(n_clicks, start_date, end_date, selected_cluster, queue_list):
	if start_date is not None and end_date is not None and selected_cluster is not None and queue_list is not None:
		s_date = tz.localize(dt.strptime(start_date, '%Y-%m-%d'))
		e_date = tz.localize(dt.strptime(end_date, '%Y-%m-%d'))
		print(type(queue_list))
		print(queue_list)
		print((len(queue_list) > 0))
		group_sunburst = None

		if (e_date > s_date) and (len(queue_list) > 0):
			print(queue_list)
			group_sunburst = create_group_sunburst(MEM_DB, df_config[selected_cluster], queue_list, s_date, e_date)
		return ('The selected cluster is {}. The period is from {} to {}'.format(
			selected_cluster,
			s_date.timestamp(),
			e_date.timestamp()
			),
			group_sunburst
		)
	else:
		return None, None


@app.callback(
	[dash.dependencies.Output('cluster_utilization_container_submit_button', component_property='children'),
		dash.dependencies.Output('cluster_utilization', component_property='children'),
		dash.dependencies.Output('queues_utilization', component_property='children')],
	[dash.dependencies.Input('cluster_utilization_submit_button', component_property='n_clicks')],
	[dash.dependencies.State('cluster-utilization-date-picker-range', component_property='start_date'),
		dash.dependencies.State('cluster-utilization-date-picker-range', component_property='end_date'),
		dash.dependencies.State(component_id='selected_cluster', component_property='children')])
def update_cluster_utilization(n_clicks, start_date, end_date, selected_cluster):
	if start_date is not None and end_date is not None and selected_cluster is not None:
		s_date = tz.localize(dt.strptime(start_date, '%Y-%m-%d'))
		e_date = tz.localize(dt.strptime(end_date, '%Y-%m-%d'))
		total_time = 0.0
		cluster_utilization = None
		queues_utilization = None

		if (e_date > s_date) and (s_date.replace(day=1) != e_date.replace(day=1)):
			t_start = time.time()
			[cluster_utilization, queues_utilization] = create_cluster_utilization_bars(MEM_DB, df_config[selected_cluster], s_date, e_date)
			t_end = time.time()
			total_time = t_end - t_start
		return ('The selected cluster is {}. The period is from {} to {}. Elapsed time: {} seconds'.format(
			selected_cluster,
			s_date.timestamp(),
			e_date.timestamp(),
			total_time
			),
			cluster_utilization,
			queues_utilization
		)
	else:
		return None, None, None

@app.callback(
	[dash.dependencies.Output('nodes_occupancy_container_submit_button', component_property='children'),
		dash.dependencies.Output('nodes_occupancy', component_property='children')],
	[dash.dependencies.Input('nodes_occupancy_submit_button', component_property='n_clicks')],
	[dash.dependencies.State('nodes-occupancy-date-picker-range', component_property='start_date'),
		dash.dependencies.State('nodes-occupancy-date-picker-range', component_property='end_date'),
		dash.dependencies.State(component_id='selected_cluster', component_property='children')])
def update_nodes_occupancy(n_clicks, start_date, end_date, selected_cluster):
	if start_date is not None and end_date is not None and selected_cluster is not None:
		s_date = tz.localize(dt.strptime(start_date, '%Y-%m-%d'))
		e_date = tz.localize(dt.strptime(end_date, '%Y-%m-%d'))
		total_time = 0.0
		nodes_occupancy = None

		if e_date > s_date:
			t_start = time.time()
			nodes_occupancy = create_nodes_occupancy_bars(MEM_DB, df_config[selected_cluster], s_date, e_date)
			t_end = time.time()
			total_time = t_end - t_start
		return ('The selected cluster is {}. The period is from {} to {}. Elapsed time: {} seconds'.format(
			selected_cluster,
			s_date.timestamp(),
			e_date.timestamp(),
			total_time
			),
			nodes_occupancy
		)
	else:
		return None, None

@app.server.route('/downloads/<path:path>')
def serve_static(path):
	root_dir = os.getcwd()
	return flask.send_from_directory(
		os.path.join(root_dir, 'downloads'), path
	)


if __name__ == '__main__':

	print('Config File path: ' + jsonPath)
	app.run_server()
	#app.run_server(debug=False, host='0.0.0.0', port=8080)
