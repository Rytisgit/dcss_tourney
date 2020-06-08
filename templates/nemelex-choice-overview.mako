<%!
  import nemelex
  import html
%>

<%
  nem_list = nemelex.list_nemelex_choices(cursor)
  if nem_list:
    pnem_list = []
    for x in nem_list[:-1]:
      combostr = x[0] + ' (won:'
      if x[2] >= 8:
        combostr += ' <s>%d individual</s>,' % x[2]
      else:
        combostr += ' %d individual,' % x[2]
      if x[3] >= 8:
        combostr += ' <s>%d clan</s>' % x[3]
      else:
        combostr += ' %d clan' % x[3]
      combostr += ')'
      pnem_list.append(combostr)
%>
<p class="lead">
  Current combo:
  <b>
    ${nem_list[-1][0]}
  </b>
  , chosen on ${nem_list[-1][1]} UTC.
</p>
% if pnem_list:
<p>
  Previous combos:
  ${html.english_join(pnem_list)}
</p>
% endif
