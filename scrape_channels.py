import discord
import asyncio
import json
import os, sys
import argparse

from time import time

# example: python scrape_channels.py -t [token] -sid [server id]
parser = argparse.ArgumentParser(description='Scrape channel logs.')
parser.add_argument('--server_id', '-sid', type=str, help='the discord server id, required', required=True)
parser.add_argument('--token', '-t', type=str, help='token, used to log in')
parser.add_argument('--user', '-u', type=str, help='username, note: should not be used')
parser.add_argument('--password', '-p', type=str, help='password, note: should not be used')
parser.add_argument('--channels', '-c', type=str, nargs='*', help='channel ids')
parser.add_argument('--messages', '-m', type=int, help='number of messages to fetch per request')
parser.add_argument('--selfbot', action='store_true', help='is the connecting user a selfbot/regular user? note: should not be used')

SERVER_ID = ""
CHANNELS = []
SERVER = None
TIMESTAMP_STR = str(int(time()))
MESSAGES = 100  # default, use --messages or -m to change

client = discord.Client()


@client.event
async def on_ready():
	print('Logged in as: %s' % client.user.name)
	print('------')

	channels = 0
	for channel in client.get_all_channels():
		if str(channel.type) == 'text':  # and channel.permissions_for(client.user).read_message_history:
			await scrape_logs_from(channel)
			channels += 1
			
	try:
		client.close()
	except:
		pass
		
	print(f"Finished scraping {channels} channel(s).")


async def scrape_logs_from(channel):
	all_messages = []
	all_clean_messages = []
	
	log_dir = 'logs/' + channel.guild.name + '/' + TIMESTAMP_STR + '/'
	log_prefix = f"{channel.id}_{channel.name}-"
	log_suffix = '-log.txt'
	
	if not os.path.exists(log_dir):
		os.makedirs(log_dir)
	
	f_messages = open(log_dir + log_prefix + 'messages' + log_suffix, mode='w')
	f_clean_messages = open(log_dir + log_prefix + 'clean-messages' + log_suffix, mode='w')
	
	print('scraping logs for %s' % channel.name)
	
	last = channel.created_at
	total = 0
	
	while True:
		messages = await channel.history(after=last, limit=MESSAGES).flatten()

		if len(messages) == 0:
			break
			
		await write_messages(messages, f_messages, f_clean_messages)
		last = messages[0]
		total += len(messages)
		print("%d messages scraped" % total)
		
	f_messages.close()
	f_clean_messages.close()
	
	print("\nDone writing messages for %s.\n" % channel.name)


async def write_messages(messages, f_messages, f_clean_messages):
	for message in messages[::-1]:
		f_messages.write(json.dumps({
			'id': message.id,
			'timestamp': str(message.created_at),
			'edited_timestamp': str(message.edited_at),
			'author_id': message.author.id, 
			'author_name': message.author.name, 
			'content': message.content
		}, sort_keys=True) + '\n')
		
		f_clean_messages.write(json.dumps({
			'id': message.id,
			'clean_content': message.clean_content
		}, sort_keys=True) + '\n')


args = parser.parse_args()

if args.server_id:
	SERVER_ID = args.server_id
if args.channels:
	CHANNELS = args.channels
if args.messages:
	if 0 < args.messages <= 100:
		MESSAGES = args.messages
	else:
		print("Max number of messages to return (1-100), using default: %d" % MESSAGES)

if args.selfbot:
	print("Using self-bots is not recommended.")
	if args.token:
		client.run(args.token, bot=False)
	elif args.user and args.password:
		print("Using user/password is not recommended.")
		client.run(args.user, args.password)
elif args.token:
	client.run(args.token)
elif args.user or args.password:
	print("If you're using user/password, you need to use --selfbot, note: this probably breaks discord ToS")
	sys.exit(0)
