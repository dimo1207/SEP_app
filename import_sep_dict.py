import requests
import html
import pickle

def create_SEP_dict(pickled=False):
	# r = requests.get('https://plato.stanford.edu/contents.html')
	# content = r.text
	# pickle.dump(content, open('sep_content.pickle', 'wb'))
	content = pickle.load(open('sep_content.pickle', 'rb'))
	idx1 = content.find('<div id="content">')
	content = content[idx1:]
	idx2 = content.find('</div>')
	content = content[:idx2]

	lines = [line.split('<li>') for line in content.split('</li>')]

	for line in lines:
		if len(line) > 1:
			for content in line:
				if 'jump' in content:
					line.remove(content)

	for line in lines:
		if line[0] == '\n' or line[0] == '\n   ':
			line.remove(line[0])

	del lines[0][0] # Removes unnecessary items
	del lines[-1]

	for line in lines:
		for x in line: # handles Ibn Sina (Avicenna) special case
			if '<ul>' in x and '</ul>' in x:
				lines.remove(line)

	# Indexes lists which include sublists; indexes the sublists afterwards
	indexes, indexes1, indexes2 = [], [], []
	for line in lines:
		for x in line:
			if '<ul>' in x:
				idx = lines.index(line) # Indexes the beginning of sublist
				indexes1.append(idx)
			if '</ul>' in x:
				idx2 = lines.index(line)
				indexes2.append(idx2)
				lines[idx2].clear() # keeps the loop from indexing the same item repeatedly

	# Creates a list of tuples containing the starting and ending sublist indexes
	for i in range(len(indexes1)):
		indexes.append((indexes1[i], indexes2[i]))

	# Extends previously indexed lists with their appropriate sublists:
	for i in enumerate(indexes):
		idx1 = indexes[i[0]][0]
		idx2 = indexes[i[0]][1]
		if idx2 - idx1 > 1:
			for x in range(idx1+1, idx2):
				lines[idx1].extend(lines[x])
				lines[x].clear()
		else:
			lines[idx1].extend(lines[idx2])
			lines[idx2].clear()


	working_content, final_group = [], []
	for line in lines:
		line = [html.unescape(x) for x in line]
		if len(line) == 1:
			if line[0].startswith(' <a href="'):
				line[0] = line[0].replace(' <a href="', '').strip(' ')
			if 'see' in line[0]:
				line = line[0].split(' — ')
				i = line[1].index('<')
				x = line[1].index('>')
				link = line[1][i+8:x-1]
				line[1] = line[1][:i] + line[1][x+1:-5]
				if '<em>' in line[0]:
					line[0] = line[0].strip(' ').replace('<em>', '').replace('</em>', '')
				if '<em>' in line[1]:
					clean = line[1].replace('<em>', '').replace('</em>', '')
					inner_dict = {clean: link.strip('"')}
					final_dict = {line[0].strip(' '): inner_dict}
					working_content.append(final_dict)
					continue
				inner_dict = {line[1]: link.strip('"')}
				final_dict = {line[0].strip(' '): inner_dict}
				working_content.append(final_dict)
			else:
				i = line[0].index('<')
				link = line[0][:i-2]
				x = line[0].index('</strong>')
				line[0] = line[0][i+8:x] + line[0][x+13:]
				if '<em>' in line[0]:
					line[0] = line[0].replace('<em>', '').replace('</em>', '')
				final_dict = {line[0]: link}
				working_content.append(final_dict)

		elif len(line) == 2:
			if line[0].startswith(' <a href="'):
				line[0] = line[0].replace(' <a href="', '').replace('\n   <ul>\n   ', '')
				i = line[0].index('<strong>')
				x = line[0].index('</strong>')
				link = line[0][:i-2]
				title = line[0][i+8:x] + line[0][x+13:]
				if '<em>' in title: # handles the "Principia" special case
					title = title.replace('<em>', '').replace('</em>', '')
				final_dict = {title: link}
				working_content.append(final_dict)

			elif line[1].startswith(' <a href="'):
				line[1] = line[1].replace(' <a href="', '')
				l = line[1].index('"') # indexes the end of the link
				link = line[1][:l] # stores the link
				i = line[1].index('<strong>')
				x = line[1].index('</strong>')
				inner_title = line[1][i+8:x] + line[1][x+13:-1]

				if line[0].endswith('\n   <ul>\n   '):
					line[0] = line[0].rstrip('\n   <ul>\n   ')
					title = line[0].strip(' ')

				if '<a href=' in line[0]:
					title = line[0].split(' — ')
					i = title[1].index('=')
					s = title[1].index('<')
					x = title[1].index('>')
					title[1] = title[1].rstrip('</a')
					second_title = title[1][:s] + title[1][x+1:]
					inner_link = title[1][i+1:x].strip('"')

					line[0] = line[0][:s] + line[0][x+1:]
					inner_dict = {second_title: inner_link}
					final_dict = {title[0].lstrip(' '): inner_dict}
					special_dict = {title[0].lstrip(' ') + ' — ' + inner_title: link}
					working_content.append(final_dict)
					working_content.append(special_dict)
					continue

				inner_dict = {inner_title: link}
				final_dict = {title: inner_dict}
				working_content.append(final_dict)

			else:			
				line[0] = line[0].rstrip('\n   <ul>\n   ').strip(' ')
				line[1] = line[1].strip(' ').rstrip('</a> ')
				i = line[1].index('=')
				s = line[1].index('<')			
				x = line[1].index('>')
				deep_link = (line[1][i+1:x]).strip('"')
				line[1] = line[1][:s] + line[1][x+1:]
				if '—' in line[0]:
					title = line[0].split(' — ')
					i = title[1].index('=')
					s = title[1].index('<')
					x = title[1].index('>')
					inner_title = title[1][:s] + title[1][x+1:].strip('</a')
					inner_title_link = title[1][i+1:x].strip('"')
					inner_title_dict = {inner_title: inner_title_link}
					if '—' in line[1]:
						second_title = line[1].split(' — ')
						second_description = second_title[1]
						second_title = second_title[0]					
						outer_dict = {second_description: deep_link}
						final_dict = {title[0]: inner_title_dict} 
						special_dict = {title[0] + ' — ' + second_title: outer_dict}
						working_content.append(final_dict)
						working_content.append(special_dict)
						continue
				inner_dict = {line[1]: deep_link}
				final_dict = {line[0]: inner_dict}
				working_content.append(final_dict)

		elif len(line) > 2:
			group = []
			for l in line:
				if '<ul>' in l: # This picks out title items
					l = l.rstrip(' <ul>\n')
					if l.startswith(' <a href="'):
						ls = l.replace(' <a href="', '').split('"')
						link = ls[0]
						i = ls[1].index('<strong>')			
						x = ls[1].index('</strong>')
						title = ls[1][i+8:x] + ls[1][x+9:].replace('</a>', '').rstrip(' ')
						title_dict = {title: link}
						group.append(title_dict)

					elif 'see' in l:
						see = l.split(' — ')
						i = see[1].index('<')
						x = see[1].index('>')
						link = see[1][i+8:x-1].strip('"')
						inner_title = see[1][:i] + see[1][x+1:-3]
						title = see[0].lstrip(' ')
						inner_dict = {inner_title: link}
						title_dict = {title: inner_dict}
						group.append(title_dict)

					else:
						list_header = {l.lstrip(' '): None}
						group.append(list_header)

				else: # This picks out sub-listed items
					if l.startswith(' <a href="'):
						ls = l.replace(' <a href="', '').split('"')
						link = ls[0]
						i = ls[1].index('<strong>')			
						x = ls[1].index('</strong>')
						title = ls[1][i+8:x] + ls[1][x+9:].replace('</a>', '').rstrip(' ')
						title_dict = {title: link}
						group.append(title_dict)

					elif 'see' in l:
						see = l.strip(' ').split(' — ')
						i = see[1].index('<')
						x = see[1].index('>')
						link = see[1][i+8:x-1].strip('"')
						inner_title = see[1][:i] + see[1][x+1:-4]
						title = see[0].lstrip(' ')
						inner_dict = {inner_title: link}
						title_dict = {title: inner_dict}
						group.append(title_dict)
			final_group.append(group)

		else: # These are all empty lists
			pass

	# Final organization step before being appended to 'working_content':
	final_dict = {}
	for item in final_group:
		keys, values = [], []
		for title_key in item[0].keys():
			for i in range(1, len(item)):
				for key in item[i].keys():
					keys.append(key)
				for value in item[i].values():
					values.append(value)
		final_dict[title_key] = {key: value for key, value in zip(keys, values)}

	for key, value in zip(final_dict.keys(), final_dict.values()):
		working_content.append({key: value})


	# FINAL DICTIONARY:
	SEP_dict = {}
	for line in working_content:
		SEP_dict.update(line)

	if pickled is True:
		pickle.dump(SEP_dict, open('SEP_dict.pickle', 'wb'))

	return SEP_dict


if __name__ == '__main__':
	SEP_dict = create_SEP_dict(pickled=False)
	# link = SEP_dict[ENTER KEY]
	# URL = 'https://plato.stanford.edu/{}'.format(link)

	# for key in sorted(SEP_dict.keys()):
	# 	print(key)