#!/usr/bin/python

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
import getpass
import re
import os
import mysql.connector

EMAIL = "bamelegari@alaska.edu"
FILE_PREFIX = "templates/grade9-8_"
pwd = getpass.getpass("enter password for " + EMAIL + ": ")

def getEmail():
	x = raw_input("Enter student's email address: ")
	if not re.match(r"[^@]+@[^@]+\.[^@]+", x):
		print("not an email address")
		return getEmail()
	else:
		return x

def getPassStatus():
	x = raw_input("Did the student...\n [1] Pass\n [2] Almost pass\n [3] Fail\n")
	x = int(x)
	if x != 1 and x != 2 and x != 3:
		print("invalid pass status")
		return getPassStatus()
	else:
		return x

def isInt(c):
	try:
		int(c)
		return True
	except ValueError:
		return False


def inputScore(gradeNum):
	x = raw_input("Enter grade " + gradeNum + " test score, out of 50: ")

	if not isInt(x):
		print("invalid test score")		#DON'T REFACTOR THIS OUT
		return inputScore(gradeNum)		#it needs to be separate from the check below

	if int(x) > 50 or int(x) < 0:
		print("invalid test score")
		return inputScore(gradeNum)
	else:
		return x

def getTemplateString(templateName):
	f = open(FILE_PREFIX + templateName + ".txt", 'r')
	templateString = f.read()
	return templateString

def inputWrongQuestions(questionsWrong):
	arr = []
	i = 0

	while i < questionsWrong:
		n = raw_input("enter incorrect question number: ")

		if not isInt(n):
			print("invalid question number, try again...")		#DON'T REFACTOR THIS OUT
																#it needs to be separate from the check below
		elif int(n) < 1 or int(n) > 50:
			print("invalid question number, try again...")
		elif n in arr:
			print("question number already entered, try again...")
		else:
			arr.append(n)
			i += 1

	return arr

def answerYes():
	ans = raw_input()
	if ans == 'y' or ans == 'Y' or ans == 'yes':
		return True
	elif ans == 'n' or ans == 'N' or ans == 'no':
		return False
	else:
		print("invalid answer...")
		return answerYes()

def prepareForAttachment(filename):
	filePath = "attachments/" + filename
	fd = open(filePath, 'rb')
	part = MIMEBase('application', 'octet-stream')
	part.set_payload(fd.read())
	encoders.encode_base64(part)
	part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
	return part

def sendEmail(msg, addrs):
	print("Handshaking...")
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	print("Authenticating...")
	s.login(EMAIL, pwd)
	print("Sending email...")
	s.sendmail(EMAIL, addrs, msg.as_string())
	print("Closing connection.")
	s.quit()
	return

def sendFollowup(addrs):
	msg = MIMEMultipart()
	msg['From'] = EMAIL

	if type(addrs) is list:
		msg['To'] = ", ".join(addrs)
	else:
		msg['To'] = addrs
		
	msg['Subject'] = "Referee certification follow-up"
	msg.attach(MIMEText(getTemplateString("followup"), 'plain'))

	a = prepareForAttachment("GO_register.pdf")
	msg.attach(a)
	sendEmail(msg, addrs)
	return

#def mysqlStart():

def main():
	name = raw_input("Enter student first name: ")

	studentEmail = getEmail()
	print("Is there a second email address? [y,n]")
	secondEmail = answerYes()
	if secondEmail:
		studentEmail2 = getEmail()

	studentPassStatus = getPassStatus()

	grade9Score = inputScore('9')
	if int(grade9Score) < 50:
		grade9WrongQuestions = inputWrongQuestions(50 - int(grade9Score))

	grade8Score = inputScore('8')
	print("Did student get question 29 wrong? [y,n]")
	twentyNineWrong = answerYes()
	if int(grade8Score) < 50:
		if twentyNineWrong:
			grade8WrongQuestions = inputWrongQuestions(50 - int(grade8Score) + 1)
		else:
			grade8WrongQuestions = inputWrongQuestions(50 - int(grade8Score))
	elif twentyNineWrong:	#29 was wrong but they got all others right (score = 50)
		grade8WrongQuestions = ["29"]

	if studentPassStatus == 1:
		emailBody = getTemplateString("pass")
	elif studentPassStatus == 2:
		emailBody = getTemplateString("almost")
	else: #studentPassStatus == 3
		emailBody = getTemplateString("fail")

	emailBody = emailBody.replace("NAME", name)
	emailBody = emailBody.replace("G9_SCORE", grade9Score)
	emailBody = emailBody.replace("G8_SCORE", grade8Score)

	if int(grade9Score) < 50:
		emailBody = emailBody.replace("G9_QUESTIONS", "Grade 9 Questions:\n" + ", ".join(grade9WrongQuestions))
	else:
		emailBody = emailBody.replace("G9_QUESTIONS", "(NONE)")

	if int(grade8Score) < 50 or twentyNineWrong:
		emailBody = emailBody.replace("G8_QUESTIONS", "Grade 8 Questions:\n" + ", ".join(grade8WrongQuestions))
	else:
		emailBody = emailBody.replace("G8_QUESTIONS", "(NONE)")

	print("do you want to add any notes about specific questions or other things?")
	notes = ""
	if answerYes():
		notes = raw_input("add notes here:")

	emailBody = emailBody.replace("NOTES", notes)

	print("\n\nPlease review the following generated email. Is it correct?\n\n")

	print(emailBody + '\n\n' + "good? [y, n]")

	if not answerYes():
		print("restarting...")
		main()

	msg = MIMEMultipart()
	msg['From'] = EMAIL
	if secondEmail:
		msg['To'] = ", ".join([studentEmail, studentEmail2])
	else:
		msg['To'] = studentEmail

	msg['Subject'] = "Referee Tests"

	msg.attach(MIMEText(emailBody, 'plain'))

	g9Attachment = prepareForAttachment("grade9Test.pdf")
	g8Attachment = prepareForAttachment("grade8Test.pdf")
	msg.attach(g9Attachment)
	msg.attach(g8Attachment)

	if secondEmail:
		sendEmail(msg, [studentEmail, studentEmail2])
	else:
		sendEmail(msg, studentEmail)

	if studentPassStatus == 1:
		print("Do you want to send this passing student a follow-up? [y,n]")
		if answerYes():
			if secondEmail:
				sendFollowup([studentEmail, studentEmail2])
			else:
				sendFollowup(studentEmail)


	print("Is there another student you need to process? [y,n]")
	if answerYes():
		main()
	return

#initial call only
main()