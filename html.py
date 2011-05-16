import query, crawl_utils, time
import loaddb
import sys

from crawl_utils import clan_link, player_link, linked_text
import re

BANNER_IMAGES = \
    { 'temple': [ 'banner_temple.png', 'Temple' ],
      'orc': [ 'banner_orc.png', 'Orc' ],
      'lair': [ 'banner_lair.png', 'Lair' ],
      'hive': [ 'banner_hive.png', 'Hive' ],
      'vaults': [ 'banner_vaults.png', 'Vaults' ],
      'hell': [ 'banner_hell.png', 'Hell' ],
      'pan': [ 'banner_pan.png', 'Pan' ],
      'abyss': [ 'banner_abyss.png', 'Abyss' ],
      'zot': [ 'banner_zot.png', 'Zot' ],
      'top_player_Nth:1': [ '1player.png', 'Best Player: 1st' ],
      'top_player_Nth:2': [ '2player.png', 'Best Player: 2nd' ],
      'top_player_Nth:3': [ '3player.png', 'Best Player: 3rd' ],
      'top_clan_Nth:1':   [ '1clan.png', 'Best Clan: 1st' ],
      'top_clan_Nth:2':   [ '2clan.png', 'Best Clan: 2nd' ],
      'top_clan_Nth:3':   [ '3clan.png', 'Best Clan: 3rd' ],
    }

STOCK_WIN_COLUMNS = \
    [ ('player', 'Player'),
      ('score', 'Score', True),
      ('charabbrev', 'Character'),
      ('turn', 'Turns'),
      ('duration', 'Duration'),
      ('god', 'God'),
      ('runes', 'Runes'),
      ('end_time', 'Time', True)
    ]

EXT_WIN_COLUMNS = \
    [ ('score', 'Score', True),
      ('race', 'Species'),
      ('class', 'Class'),
      ('god', 'God'),
      ('title', 'Title'),
      ('xl', 'XL'),
      ('turn', 'Turns'),
      ('duration', 'Duration'),
      ('runes', 'Runes'),
      ('end_time', 'Date')
    ]

STOCK_COLUMNS = \
    [ ('player', 'Player'),
      ('score', 'Score', True),
      ('charabbrev', 'Character'),
      ('place', 'Place'),
      ('verb_msg', 'Death'),
      ('turn', 'Turns'),
      ('duration', 'Duration'),
      ('god', 'God'),
      ('runes', 'Runes'),
      ('end_time', 'Time', True)
    ]

EXT_COLUMNS = \
    [ ('score', 'Score', True),
      ('race', 'Species'),
      ('class', 'Class'),
      ('god', 'God'),
      ('title', 'Title'),
      ('place', 'Place'),
      ('verb_msg', 'Death'),
      ('xl', 'XL'),
      ('turn', 'Turns'),
      ('duration', 'Duration'),
      ('runes', 'Runes'),
      ('end_time', 'Date')
    ]

WHERE_COLUMNS = \
    [ ('race', 'Species'),
      ('cls', 'Class'),
      ('god', 'God'),
      ('title', 'Title'),
      ('place', 'Place'),
      ('xl', 'XL'),
      ('turn', 'Turns'),
      ('time', 'Time'),
      ('status', 'Status')
    ]

R_STR_DATE = re.compile(r'^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})')

def fixup_column(col, data, game):
  if col.find('time') != -1:
    return pretty_date(data)
  elif col.find('duration') != -1:
    return pretty_dur(data)
  elif col == 'place' and game.get('killertype') == 'winning':
    return ''
  return data

def pretty_dur(dur):
  if not dur:
    return ""
  try:
    secs = dur % 60
  except:
    print "FAIL on %s" % dur
    raise
  dur /= 60
  mins = dur % 60
  dur /= 60
  hours = dur
  stime = "%d:%02d:%02d" % (hours, mins, secs)

  return stime

def pretty_date(date):
  if not date:
    return ''

  if type(date) in [str, unicode]:
    m = R_STR_DATE.search(date)
    if not m:
      return date
    return "%s-%s-%s %s:%s:%s" % (m.group(1), m.group(2), m.group(3),
                                  m.group(4), m.group(5), m.group(6))

  return "%04d-%02d-%02d %02d:%02d:%02d" % (date.year, date.month, date.day,
                                            date.hour, date.minute,
                                            date.second)

def pretty_time(time):
  return "%04d-%02d-%02d %02d:%02d:%02d" % (time.tm_year, time.tm_mon,
                                            time.tm_mday,
                                            time.tm_hour, time.tm_min,
                                            time.tm_sec)

def update_time():
  return '''<div class="updatetime">
            Last updated %s UTC.
            </div>''' % pretty_time(time.gmtime())

def wrap_tuple(x):
  if isinstance(x, tuple):
    return x
  else:
    return (x,)

def is_player_header(header):
  return header in ['Player', 'Captain']

def is_clan_header(header):
  return header in ['Clan', 'Team', 'Teamname']


def table_text(headers, data, cls='bordered', count=True, link=None,
               width=None, place_column=-1, stub_text='No data', skip=False):
  if cls:
    cls = ''' class="%s"''' % cls
  if width:
    width = ' width="%s%%"' % width
  out = '''<table%s%s>\n<tr>''' % (cls or '', width or '')

  headers = [ wrap_tuple(x) for x in headers ]

  if count:
    out += "<th></th>"
  for head in headers:
    out += "<th>%s</th>" % head[0]
  out += "</tr>\n"
  odd = True

  nrow = 0

  ncols = len(headers) + (count and 1 or 0)
  if not data:
    out += '''<tr><td colspan='%s'>%s</td></tr>''' % (ncols, stub_text)

  nplace = 0
  rplace = 0
  last_value = None

  for row in data:
    nrow += 1
    out += '''<tr class="%s">''' % (odd and "odd" or "even")
    odd = not odd

    rplace += 1
    if place_column == -1:
      nplace += 1
    elif last_value != row[place_column]:
      nplace += 1
      if skip:
        nplace = rplace
      last_value = row[place_column]

    if count:
      out += '''<td class="numeric">%s</td>''' % nplace

    for c in range(len(headers)):
      val = row[c]
      header = headers[c]
      tcls = (isinstance(val, str) and not val.endswith('%')) \
          and "celltext" or "numeric"
      out += '''<td class="%s">''' % tcls
      val = str(val)
      if is_player_header(header[0]):
        val = linked_text(val, player_link)
      out += val
      out += '</td>'
    out += "</tr>\n"
  out += '</table>\n'
  return out

def games_table(games, first=None, excluding=None, columns=None,
                including=None,
                cls='bordered', count=True, win=True):
  columns = columns or (win and STOCK_WIN_COLUMNS or STOCK_COLUMNS)

  # Copy columns.
  columns = list(columns)

  if excluding:
    columns = [c for c in columns if c[0] not in excluding]

  if including:
    for pos, col in including:
      columns.insert(pos, col)

  if first and not isinstance(first, tuple):
    first = (first, 1)

  if first and columns[0][0] != first[0]:
    firstc = [ c for c in columns if c[0] == first[0] ]
    columns = [ c for c in columns if c[0] != first[0] ]
    columns.insert( first[1], firstc[0] )

  if cls:
    cls = ''' class="%s"''' % cls
  out = '''<table%s>\n<tr>''' % (cls or '')
  if count:
    out += "<th></th>"
  for col in columns:
    out += "<th>%s</th>" % col[1]
  out += "</tr>\n"
  odd = True
  ngame = 0

  ncols = len(columns) + (count and 1 or 0)
  if not games:
    out += '''<tr><td colspan='%s'>No games</td></tr>''' % ncols

  for game in games:
    ngame += 1

    ocls = odd and "odd" or "even"
    if game.get('killertype') == 'winning':
      ocls += " win"

    out += '''<tr class="%s">''' % ocls
    odd = not odd

    if count:
      out += '''<td class="numeric">%s</td>''' % ngame

    for c in columns:
      val = fixup_column(c[0], game.get(c[0]) or '', game)
      tcls = isinstance(val, str) and "celltext" or "numeric"
      out += '''<td class="%s">''' % tcls

      need_link = len(c) >= 3 and c[2]
      if need_link:
        try:
          out += r'<a href="%s">' % crawl_utils.morgue_link(game)
        except:
          sys.stderr.write("Error processing game: " + loaddb.xlog_str(game))
          raise
      elif is_player_header(c[1]):
        val = linked_text(val, player_link)
      out += str(val)
      if need_link:
        out += '</a>'
      out += '</td>'
    out += "</tr>\n"
  out += "</table>\n"
  return out

def full_games_table(games, **pars):
  if not pars.get('columns'):
    if pars.has_key('win'):
      win = pars['win']
    else:
      win = True
    pars['columns'] = win and EXT_WIN_COLUMNS or EXT_COLUMNS
  return games_table(games, **pars)

def ext_games_table(games, win=True, **pars):
  cols = win and EXT_WIN_COLUMNS or EXT_COLUMNS
  pars.setdefault('including', []).append((1, ('player', 'Player')))
  return games_table(games, columns=cols, count=False, **pars)

def combo_highscorers(c):
  hs = query.get_top_combo_highscorers(c)
  return table_text( [ 'Player', 'Combo scores' ],
                     hs, place_column=1, skip=True )

def deepest_xl1_games(c):
  games = query.get_deepest_xl1_games(c)
  return games_table(games, first = 'place', win=False)

def most_pacific_wins(c):
  games = query.most_pacific_wins(c)
  return games_table(games,
                     columns = STOCK_WIN_COLUMNS + [('kills', 'Kills')])

def hyperlink_games(games, field):
  hyperlinks = [ crawl_utils.morgue_link(g) for g in games ]
  text = [ '<a href="%s">%s</a>' % (link, g[field])
           for link, g in zip(hyperlinks, games) ]
  return ", ".join(text)

def best_ziggurats(c):
  ziggurats = query.get_top_ziggurats(c)

  def fixup_ziggurats(zigs):
    for z in zigs:
      z[2] = pretty_date(z[2])
    return zigs

  return table_text( [ 'Player', 'Ziggurat Depth', 'Time' ],
                     fixup_ziggurats(ziggurats) )

def youngest_rune_finds(c):
  runes = query.youngest_rune_finds(c)
  runes = [list(r) for r in runes]
  for r in runes:
    r[3] = pretty_date(r[3])
  return table_text([ 'Player', 'Rune', 'XL', 'Time' ], runes)

def most_deaths_to_uniques(c):
  rows = query.most_deaths_to_uniques(c)
  for r in rows:
    r.insert(1, len(r[1]))
    r[2] = ", ".join(r[2])
  return table_text([ 'Player', '#', 'Uniques', 'Time'], rows)

def streak_table(streaks, active=False):
  # Replace the list of streak games with hyperlinks.
  result = []
  for s in streaks:
    games = s[3]
    game_text = hyperlink_games(games, 'charabbrev')
    if active:
      game_text += ", " + s[4]
    row = [s[0], s[1], pretty_date(games[0]['start_time']),
           pretty_date(s[2]), game_text]
    result.append(row)

  return table_text( [ 'Player', 'Streak', 'Start',
                       active and 'Last Win' or 'End', 'Games' ],
                     result )

def best_active_streaks(c):
  return streak_table(query.get_top_active_streaks(c), active=True)

def best_streaks(c):
  streaks = query.get_top_streaks(c)
  return streak_table(streaks)

def fixup_clan_rows(rows):
  rows = [ list(r) for r in rows ]
  for clan in rows:
    clan[0] = linked_text(clan[1], clan_link, clan[0])
  return rows

def best_clans(c):
  clans = fixup_clan_rows(query.get_top_clan_scores(c))
  return table_text( [ 'Clan', 'Captain', 'Points' ],
                     clans, place_column=2, skip=True )

def clan_unique_kills(c):
  ukills = fixup_clan_rows(query.get_top_clan_unique_kills(c))
  return table_text( [ 'Clan', 'Captain', 'Kills', 'Time' ],
                     ukills)

def clan_combo_highscores(c):
  return table_text( [ 'Clan', 'Captain', 'Scores' ],
                     fixup_clan_rows(query.get_top_clan_combos(c)),
                     place_column=2, skip=True )

def clan_affiliation(c, player, include_clan=True):
  # Clan affiliation info is clan name, followed by a list of players,
  # captain first, or None if the player is not in a clan.
  clan_info = query.get_clan_info(c, player)
  if clan_info is None:
    return "None"

  clan_name, players = clan_info
  if include_clan:
    clan_html = linked_text(players[0], clan_link, clan_name) + " - "
  else:
    clan_html = ''

  plinks = [ linked_text(players[0], player_link) + " (captain)" ]

  other_players = sorted(players[1:])
  for p in other_players:
    plinks.append( linked_text(p, player_link) )

  clan_html += ", ".join(plinks)
  return clan_html

def whereis(c, *players):
  miles = ''
  for p in players:
    where = query.whereis_player(c, p)
    if not where:
      continue
    if where[4] == None:
      god_phrase = ''
    else:
      god_phrase = ' of %s' % where[4] 
    where = where[0:4] + (god_phrase, ) + where[5:8] + (pretty_dur(where[8]), )
    miles = miles + ("%s the %s (L%d %s%s) %s (%s, turn %d, dur %s)<br />" % where)
  return miles

def _strip_banner_suffix(banner):
  if ':' in banner:
    return banner[ : banner.index(':')]
  return banner

def banner_suffix(banner):
  if ':' in banner:
    return banner[banner.index(':') + 1 :]
  return ''

def banner_image(banner, full_name=False):
  name_suffix = banner_suffix(banner)
  banner_subkey = _strip_banner_suffix(banner)
  img = BANNER_IMAGES.get(banner) or BANNER_IMAGES.get(banner_subkey)
  name = ''
  if img:
    name = img[1]
  if full_name and name_suffix:
    name = name + " (" + name_suffix + ")"
  if img and img[0]:
    return (crawl_utils.banner_link(img[0]), name)
  return img

def banner_img_for(b, nth):
  if nth:
    bid = " id=\"banner-%d\" " % nth
  else:
    bid = ""
  return '''<div>
              <img src="%s" alt="%s"
                   title="%s" width="150" height="55"
                   %s class="banner">
            </div>''' % (b[0], b[1], b[1], bid)

def banner_named(name):
  img = banner_image(name)
  if not img:
    return None
  return banner_img_for(img, 0)

def banner_images(banners):
  images = [banner_image(x) for x in banners]
  images = [i for i in images if i and i[0]]
  seen_images = set()
  deduped = []
  for i in images:
    if not i[1] in seen_images:
      deduped.append(i)
      seen_images.add(i[1])
  return deduped

def banner_div(all_banners):
  res = ''
  banner_n = 1
  for b in all_banners:
    res += banner_img_for(b, banner_n)
    banner_n += 1
  return res

def _scored_win_text(g, text):
  if g['killertype'] == 'winning':
    text += '*'
  return text

def player_combo_scores(c, player):
  games = query.get_combo_scores(c, player=player)
  games = [ [ crawl_utils.linked_text(g, crawl_utils.morgue_link,
                                      _scored_win_text(g, g['charabbrev'])),
              g['score'] ]
            for g in games ]
  return games

def player_species_scores(c, player):
  games = query.game_hs_species(c, player)

  games = [
    [ crawl_utils.linked_text(g, crawl_utils.morgue_link,
                              _scored_win_text(g, g['charabbrev'][:2])),
      g['score'] ]
    for g in games ]
  return games

def player_class_scores(c, player):
  games = query.game_hs_classes(c, player)
  games = [
    [ crawl_utils.linked_text(g, crawl_utils.morgue_link,
                              _scored_win_text(g, g['charabbrev'][2:])),
      g['score'] ]
    for g in games ]
  return games

def player_scores_block(c, scores, title):
  asterisk = [ s for s in scores if '*' in s[0] ]
  score_table = (scores
                 and (", ".join([ "%s&nbsp;(%d)" % (s[0], s[1])
                                  for s in scores ]))
                 or "None")
  text = """<h3>%(title)s</h3>
              <div class="inset inline bordered">
                %(score_table)s
              </div>
         """ % {'title': title, 'score_table': score_table}
  if asterisk:
    text += "<p class='fineprint'>* Winning Game</p>"
  return text
