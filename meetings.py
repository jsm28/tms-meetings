#! /usr/bin/python3

import argparse
import datetime
import html
import re
import xml.etree.ElementTree


nbsp = '\u00a0'
ndash = '\u2013'
mdash = '\u2014'
rsquo = '\u2019'
ldquo = '\u201c'
rdquo = '\u201d'
joint_societies = ('Adams Society', 'Archimedeans', 'Magpie and Stump',
                   'Mathematics Research Students'+rsquo+' Tea Club',
                   'New Pythagoreans', 'Trinity College Music Society',
                   'Trinity College Natural Sciences Society',
                   'Trinity College Science Society')
# Titles are expected to come from this list, in order.  The common
# British convention is used where such full stops are not used for
# abbreviations ending with the last letter of the word abbreviated.
pers_titles = ('Prof. ', 'Rev. ', 'Dr ', 'Hon. ', 'Col. ', 'Sir ',
               'Lord ', 'Mr ', 'Mrs ', 'Ms ', 'Miss ')
roles = ('proponent', 'opponent', 'author', 'producer')
meeting_types = ('talk', 'talks', 'sporting event', 'dinner', 'debate',
                 'inaugural meeting', 'planning meeting', 'film night',
                 'panel discussion', 'opera', 'photograph', 'recreational',
                 'visit', 'general meeting', 'business meeting', 'discussion',
                 'symposium')
meeting_flags = ('non-election business', 'election of officers',
                 'televised')
venues = ('',
          'Adrian House Seminar Room',
          'the College Bar (Q1 Great Court, 1958'+ndash+'1998)',
          'Babbage Lecture Theatre',
          'Bar',
          'Blue Boar Common Room',
          'Brewhouse Marquee',
          'Burrell'+rsquo+'s Field Common Room',
          'Butler House Party Room',
          'Caius College',
          'river Cam',
          'Christ'+rsquo+'s College',
          'DAMTP',
          'Emmanuel College',
          'Hall',
          'Junior Combination Room',
          'Junior Parlour',
          'Lecture-Room Theatre (I Great Court)',
          'Lecture Rooms (I Great Court)',
          'Master'+rsquo+'s Lodge',
          'Old Combination Room',
          'Old Field',
          'Old Kitchens',
          'Private Supply Room',
          'St John'+rsquo+'s College',
          'Winstanley Lecture Theatre',
          'Wolfson Party Room',
          'Zoom')
venues_re = ('.* Blue Boar Court',
             'Room .*, 4A Bridge Street',
             '.* Bishop'+rsquo+'s Hostel',
             '.* Great Court',
             '.* Whewell'+rsquo+'s Court',
             '.* New Court',
             r'Lecture Room .* \(I Great Court\)',
             'Centre for Mathematical Sciences MR.*',
             '.* Nevile'+rsquo+'s Court')


def check_title(title):
    """Check a person's title is in the expected form."""
    orig_title = title
    if title != '':
        title += ' '
    for t in pers_titles:
        if title.startswith(t):
            title = title[len(t):]
    if title != '':
        raise ValueError('unexpected title: %s' % orig_title)


def check_unicode(text):
    """Verify absence of ASCII characters where Unicode versions expected."""
    if text is None:
        return
    if '"' in text:
        raise ValueError('ASCII double quote: %s' % text)
    if "'" in text:
        raise ValueError('ASCII single quote: %s' % text)
    if '...' in text:
        raise ValueError('ASCII ellipsis: %s' % text)
    if ' -' in text:
        raise ValueError('ASCII dash: %s' % text)
    if re.search(r'[0-9]-[0-9]', text):
        raise ValueError('ASCII dash: %s' % text)
    if re.search(r'[0-9]-\Z', text):
        raise ValueError('ASCII dash: %s' % text)


class Speaker(object):
    """Title and name of a speaker, possibly with a role, at a TMS event."""

    def __init__(self, title, first, last, role):
        """Initialize a Speaker object."""
        self.title = title or ''
        check_title(self.title)
        self.first = first
        self.last = last
        self.id = '%s, %s' % (last, first)
        if role and role not in roles:
            raise ValueError('unexpected role: %s' % role)
        self.role = role

    def xml_text(self):
        """The canonical XML text of a Speaker object."""
        sp = []
        sp.append('        <stitle>%s</stitle>' % html.escape(self.title))
        sp.append('        <first>%s</first>' % html.escape(self.first))
        sp.append('        <last>%s</last>' % html.escape(self.last))
        if self.role:
            sp.append('        <role>%s</role>' % html.escape(self.role))
        return '      <speaker>\n%s\n      </speaker>' % '\n'.join(sp)

    def html_text(self, speaker_data):
        """HTML text for a Speaker object in the list of meetings."""
        name = '%s %s' % (self.first, self.last)
        name = name.replace(' ', nbsp)
        name = html.escape(name)
        if self.id in speaker_data:
            name = '<a href="%s">%s</a>' % (html.escape(speaker_data[self.id]),
                                            name)
        title = self.title.replace(' ', nbsp)
        if title:
            text = '%s%s%s' % (html.escape(title), nbsp, name)
        else:
            text = name
        if self.role:
            text = '%s (%s)' % (text, html.escape(self.role))
        return text


class SubLink(object):
    """A link to some extra document for a SubMeeting."""

    def __init__(self, desc, href):
        """Initialize a SubLink object."""
        check_unicode(desc)
        self.desc = desc
        self.href = href

    def xml_text(self):
        """The canonical XML text of a SubLink object."""
        s = []
        s.append('        <linkdesc>%s</linkdesc>' % html.escape(self.desc))
        s.append('        <href>%s</href>' % html.escape(self.href))
        return '      <link>\n%s\n      </link>' % '\n'.join(s)


class SubMeeting(object):
    """A meeting title or description with zero or more speakers."""

    def __init__(self, desc, title, note, speakers, abstract, links):
        """Initialize a SubMeeting object."""
        # A title is implicitly quoted.  A description is not quoted,
        # but may contain quoted text.  A note implicitly follows
        # afterwards in parentheses.
        if desc and title:
            raise ValueError('both description "%s" and title "%s"'
                             % (desc, title))
        check_unicode(desc)
        check_unicode(title)
        check_unicode(note)
        check_unicode(abstract)
        self.desc = desc
        self.title = title
        self.note = note
        self.speakers = speakers
        self.abstract = abstract
        self.links = links

    def xml_text(self):
        """The canonical XML text of a SubMeeting object."""
        s = []
        for speaker in self.speakers:
            s.append(speaker.xml_text())
        if self.desc:
            s.append('      <desc>%s</desc>' % html.escape(self.desc))
        if self.title:
            s.append('      <title>%s</title>' % html.escape(self.title))
        if self.note:
            s.append('      <mnote>%s</mnote>' % html.escape(self.note))
        if self.abstract:
            s.append('      <abstract>%s</abstract>'
                     % html.escape(self.abstract))
        for link in self.links:
            s.append(link.xml_text())
        return '    <sub>\n%s\n    </sub>' % '\n'.join(s)

    def html_text(self, speaker_data):
        """HTML text for a SubMeeting object in the list of meetings."""
        stext = ' and '.join([s.html_text(speaker_data)
                              for s in self.speakers])
        if self.title:
            dtext = ldquo+self.title+rdquo
        else:
            dtext = self.desc
        if self.note:
            dtext = '%s (%s)' % (dtext, self.note)
        dtext = html.escape(dtext)
        if stext:
            dtext = '%s, %s' % (stext, dtext)
        dtext += '.'
        if self.abstract:
            dtext += '<br>\nAbstract: %s' % html.escape(self.abstract)
        for link in self.links:
            dtext += '<br>\n[<a href="%s">%s</a>]' % (html.escape(link.href),
                                                      html.escape(link.desc))
        return dtext


class Meeting(object):
    """The complete record for a meeting."""

    def __init__(self, number, date, mtype, flags, joint, sub, venue,
                 attendance, volume, page):
        """Initialize a Meeting object."""
        self.number = number
        if (date != ''
            and not re.fullmatch(r'[1-9][0-9]{3}-[01?][0-9?]-[0123?][0-9?]',
                                 date)):
            raise ValueError('bad date: %s' % date)
        self.date = date
        if mtype not in meeting_types:
            raise ValueError('bad meeting type: %s' % mtype)
        self.type = mtype
        for f in flags:
            if f not in meeting_flags:
                raise ValueError('unexpected meeting flag: %s' % f)
        self.flags = flags
        for j in joint:
            if j not in joint_societies:
                raise ValueError('unexpected other society: %s' % j)
        self.joint = joint
        self.sub = sub
        if venue not in venues:
            venue_ok = False
            for v in venues_re:
                if re.fullmatch(v, venue):
                    venue_ok = True
                    break
            if not venue_ok:
                raise ValueError('bad venue: %s' % venue)
        self.venue = venue
        if (attendance != ''
            and attendance != '?'
            and not re.fullmatch(r'[1-9][0-9]*\+?', attendance)):
            raise ValueError('bad attendance: %s' % attendance)
        self.attendance = attendance
        self.volume = volume
        if (page != '-'
            and page != '?'
            and not re.fullmatch(r'[1-9][0-9]*', page)):
            raise ValueError('bad page number: %s' % page)
        self.page = page

    def xml_text(self):
        """The canonical XML text of a Meeting object."""
        m = []
        m.append('    <number>%s</number>' % html.escape(self.number))
        m.append('    <date>%s</date>' % html.escape(self.date))
        m.append('    <type>%s</type>' % html.escape(self.type))
        for f in self.flags:
            m.append('    <flag>%s</flag>' % html.escape(f))
        for j in self.joint:
            m.append('    <joint>%s</joint>' % html.escape(j))
        for s in self.sub:
            m.append(s.xml_text())
        m.append('    <venue>%s</venue>' % html.escape(self.venue))
        if self.attendance:
            m.append('    <attendance>%s</attendance>'
                     % html.escape(self.attendance))
        m.append('    <minutes><volume>%s</volume><page>%s</page></minutes>'
                 % (html.escape(self.volume), html.escape(self.page)))
        return '  <meeting>\n%s\n  </meeting>' % '\n'.join(m)

    def html_text(self, speaker_data):
        """HTML text for a Meeting object in the list of meetings."""
        if self.date == '':
            datetext = '(unknown date)'
        else:
            year = self.date[0:4]
            month = self.date[5:7]
            months = {'01': 'January',
                      '02': 'February',
                      '03': 'March',
                      '04': 'April',
                      '05': 'May',
                      '06': 'June',
                      '07': 'July',
                      '08': 'August',
                      '09': 'September',
                      '10': 'October',
                      '11': 'November',
                      '12': 'December',
                      '??': '??'}
            month = months[month]
            day = self.date[8:]
            day = day.lstrip('0')
            datetext = '%s %s %s' % (day, month, year)
        sub_text_list = [s.html_text(speaker_data) for s in self.sub]
        if len(self.sub) > 1:
            maintext = ('%s:\n<ul>\n%s\n</ul>\n'
                        % (html.escape(datetext),
                           '\n'.join(['<li>%s</li>' % s
                                      for s in sub_text_list])))
        else:
            maintext = '%s: %s<br>\n' % (html.escape(datetext),
                                         sub_text_list[0])
        if self.joint:
            jointtext = html.escape('Joint with: %s.'
                                    % ' and '.join(self.joint))
            jointtext = '<small>%s</small><br>\n' % jointtext
        else:
            jointtext = ''
        if self.flags:
            ftext = '%s; %s' % (self.type, '; '.join(self.flags))
        else:
            ftext = self.type
        vtext = 'Meeting %s (%s)' % (self.number, ftext)
        if self.venue:
            vtext += ', %s' % self.venue
        if self.attendance:
            vtext += ', attendance %s' % self.attendance
        vtext += '.'
        vtext = '<small>%s</small>' % html.escape(vtext)
        if self.page != '-':
            vtext += ('<br>\n<small>Minutes: volume %s page %s.</small>'
                      % (html.escape(self.volume), html.escape(self.page)))
        text = maintext + jointtext + vtext
        return '<li>%s</li>' % text


class Note(object):
    """A textual note in the list of meetings."""

    def __init__(self, text):
        """Initialize a Note object."""
        check_unicode(text)
        self.text = text

    def xml_text(self):
        """The canonical XML text of a Note object."""
        return '  <note>%s</note>' % html.escape(self.text)

    def html_text(self, speaker_data):
        """HTML text for a Note object in the list of meetings."""
        return '<p>(%s)</p>' % html.escape(self.text)


def speakers_from_xml(name):
    """Read the extra speaker information from an XML file."""
    # This function does not always validate that all the XML contents
    # use the expected tags and are otherwise understood.  Unexpected
    # contents may produce errors in some cases and be ignored in
    # others.  Writing the parsed contents back as XML and comparing
    # the results suffices for validation of both contents and
    # canonical formatting.
    root = xml.etree.ElementTree.parse(name).getroot()
    speaker_data = {}
    for entry in root:
        if entry.tag == 'speaker':
            speaker_id = entry.find('id').text
            link = entry.find('link').text
            if speaker_id in speaker_data:
                raise ValueError('duplicate information for: %s' % speaker_id)
            speaker_data[speaker_id] = link
        else:
            raise ValueError('unexpected tag: %s' % entry.tag)
    return speaker_data


def meetings_from_xml(name):
    """Read the list of meetings from an XML file."""
    # This function does not always validate that all the XML contents
    # use the expected tags and are otherwise understood, beyond the
    # checks made by the __init__ functions for various classes that
    # fields have valid values.  Unexpected contents may produce
    # errors in some cases and be ignored in others.  Writing the
    # parsed contents back as XML and comparing the results suffices
    # for validation of both contents and canonical formatting.
    root = xml.etree.ElementTree.parse(name).getroot()
    meeting_list = []
    for entry in root:
        if entry.tag == 'meeting':
            number = entry.find('number').text
            number = number if number else ''
            date = entry.find('date').text
            date = date if date else ''
            mtype = entry.find('type').text
            flags = [f.text for f in entry.findall('flag')]
            joint = [j.text for j in entry.findall('joint')]
            sub_xml = entry.findall('sub')
            sub = []
            for s in sub_xml:
                speakers_xml = s.findall('speaker')
                speakers = []
                for sp in speakers_xml:
                    stitle = sp.find('stitle').text
                    first = sp.find('first').text
                    last = sp.find('last').text
                    role_xml = sp.find('role')
                    role = role_xml.text if role_xml is not None else ''
                    speakers.append(Speaker(stitle, first, last, role))
                desc_xml = s.find('desc')
                desc = desc_xml.text if desc_xml is not None else ''
                title_xml = s.find('title')
                title = title_xml.text if title_xml is not None else ''
                note_xml = s.find('mnote')
                note = note_xml.text if note_xml is not None else ''
                abstract_xml = s.find('abstract')
                abstract = (abstract_xml.text
                            if abstract_xml is not None
                            else '')
                links_xml = s.findall('link')
                links = []
                for link in links_xml:
                    linkdesc = link.find('linkdesc').text
                    href = link.find('href').text
                    links.append(SubLink(linkdesc, href))
                sub.append(SubMeeting(desc, title, note, speakers, abstract,
                                      links))
            if mtype == 'talk' and len(sub) != 1:
                raise ValueError('meeting %s (talk) has multiple talks',
                                 number)
            if mtype == 'talks' and len(sub) <= 1:
                raise ValueError('meeting %s (talks) lacks multiple talks',
                                 number)
            venue = entry.find('venue').text
            venue = venue if venue else ''
            attendance_xml = entry.find('attendance')
            attendance = (attendance_xml.text
                          if attendance_xml is not None
                          else '')
            volume = entry.find('minutes/volume').text
            page = entry.find('minutes/page').text
            meeting_list.append(Meeting(number, date, mtype, flags, joint,
                                        sub, venue, attendance, volume, page))
        elif entry.tag == 'note':
            meeting_list.append(Note(entry.text))
        else:
            raise ValueError('unexpected tag: %s' % entry.tag)
    return meeting_list


def read_xml_data():
    """Read all the data from XML files."""
    meeting_list = meetings_from_xml('meetings.xml')
    speaker_data = speakers_from_xml('speakers.xml')
    known_speakers = set()
    for m in meeting_list:
        if isinstance(m, Meeting):
            for s in m.sub:
                for sp in s.speakers:
                    known_speakers.add(sp.id)
    for k in speaker_data.keys():
        if k not in known_speakers:
            raise ValueError('unknown speaker: %s' % k)
    return meeting_list, speaker_data


def meetings_to_xml(meeting_list):
    """Return the canonical XML text of the list of meetings."""
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<meetings>\n'
            '%s\n'
            '</meetings>\n'
            % '\n'.join([m.xml_text() for m in meeting_list]))


def speakers_to_xml(speaker_data):
    """Return the canonical XML text of the extra speaker information."""
    xml_list = []
    for k in sorted(speaker_data.keys()):
        xml_list.append('  <speaker>\n'
                        '    <id>%s</id>\n'
                        '    <link>%s</link>\n'
                        '  </speaker>'
                        % (html.escape(k), html.escape(speaker_data[k])))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<speakers>\n'
            '%s\n'
            '</speakers>\n'
            % '\n'.join(xml_list))


def action_reformat_xml(args):
    """Read the XML lists of speakers and meetings and write them out again."""
    mlist, sdata = read_xml_data()
    meetings_xml_text = meetings_to_xml(mlist)
    with open('meetings-new.xml', 'w', encoding='utf-8') as f:
        f.write(meetings_xml_text)
    speakers_xml_text = speakers_to_xml(sdata)
    with open('speakers-new.xml', 'w', encoding='utf-8') as f:
        f.write(speakers_xml_text)


def action_speaker_counts(args):
    """Count the number of talks by each speaker."""
    meeting_list, speaker_data = read_xml_data()
    exclude = args.exclude
    if exclude is None:
        exclude = []
    counts = {}
    for m in meeting_list:
        if not isinstance(m, Meeting):
            continue
        if m.type in exclude:
            continue
        for sub in m.sub:
            for sp in sub.speakers:
                name = sp.id
                if name not in counts:
                    counts[name] = 0
                counts[name] += 1
    sorted_speakers = sorted(counts.keys(), key=lambda s: (counts[s], s))
    sorted_list = ['%7d %s' % (counts[s], s) for s in sorted_speakers]
    sorted_text = '\n'.join(sorted_list) + '\n'
    with open('speaker-counts.txt', 'w', encoding='utf-8') as f:
        f.write(sorted_text)


def action_speaker_dates(args):
    """List speakers by the range of dates over which they have spoken."""
    meeting_list, speaker_data = read_xml_data()
    exclude = args.exclude
    if exclude is None:
        exclude = []
    dates = {}
    for m in meeting_list:
        if not isinstance(m, Meeting):
            continue
        if m.type in exclude:
            continue
        if m.date == '' or '?' in m.date:
            continue
        year = int(m.date[0:4])
        month = int(m.date[5:7])
        day = int(m.date[8:])
        date = datetime.date(year, month, day)
        for sub in m.sub:
            for sp in sub.speakers:
                name = sp.id
                if name in dates:
                    details = (dates[name][0], dates[name][1], m.date,
                               (date - dates[name][1]).days)
                else:
                    details = (m.date, date, m.date, 0)
                dates[name] = details
    sorted_speakers = sorted(dates.keys(), key=lambda s: (dates[s][3], s))
    sorted_list = [('%7d %-25s %s - %s'
                    % (dates[s][3], s, dates[s][0], dates[s][2]))
                   for s in sorted_speakers]
    sorted_text = '\n'.join(sorted_list) + '\n'
    with open('speaker-dates.txt', 'w', encoding='utf-8') as f:
        f.write(sorted_text)


def action_meetings_html(args):
    """Generate an HTML version of the list of meetings."""
    meeting_list, speaker_data = read_xml_data()
    cur_year = 0
    cur_text = ''
    cur_in_ul = False
    past_list = []
    for m in meeting_list:
        if isinstance(m, Note):
            if 'did not meet' in m.text:
                year = cur_year
            else:
                year = cur_year + 1
        else:
            if m.date == '' or '?' in m.date:
                year = cur_year
            else:
                year_num = int(m.date[0:4])
                month_num = int(m.date[5:7])
                year = year_num if month_num >= 10 else year_num - 1
        if year > cur_year:
            if cur_in_ul:
                cur_text += '\n</ul>'
            if cur_text:
                past_list.append(cur_text)
            cur_text = ('<h2>%d'+ndash+'%d</h2>') % (year, year + 1)
            cur_year = year
            cur_in_ul = False
        elif year != cur_year:
            raise ValueError('year going backwards')
        if isinstance(m, Note) and cur_in_ul:
            cur_text += '\n</ul>'
            cur_in_ul = False
        elif isinstance(m, Meeting) and not cur_in_ul:
            cur_text += '\n<ul>'
            cur_in_ul = True
        cur_text += '\n' + m.html_text(speaker_data)
    if cur_in_ul:
        cur_text += '\n</ul>'
    past_list.append(cur_text)
    html_head = ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 '
                 'Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n'
                 '<html>\n'
                 '<head>\n'
                 '<meta http-equiv="Content-Type" content="text/html; '
                 'charset=UTF-8">\n'
                 '<title>Trinity Mathematical Society meetings</title>\n'
                 '</head>\n'
                 '<body>\n'
                 '<h1>Trinity Mathematical Society meetings</h1>\n')
    with open('README', 'r', encoding='utf-8') as f:
        readme_text = f.read()
    readme_text = readme_text.replace('-', ndash)
    readme_list = readme_text.split('\n\n')
    html_head += ('<p>%s\n</p>\n<p>%s</p>\n'
                  '<p>The <a href="https://github.com/jsm28/tms-meetings">'
                  'source code</a>\n'
                  'for generating this version of the list is available.</p>\n'
                  % (html.escape(readme_list[0]), html.escape(readme_list[2])))
    html_foot = '\n</body>\n</html>\n'
    full_text = html_head + '\n'.join(past_list) + html_foot
    with open('meetings.html', 'w', encoding='utf-8') as f:
        f.write(full_text)


def main():
    """Main program."""
    parser = argparse.ArgumentParser(description='Process list of meetings')
    parser.add_argument('--exclude',
                        action='append',
                        help='Types of meetings to ignore for statistics')
    parser.add_argument('action',
                        help='What to do',
                        choices=('reformat-xml', 'speaker-counts',
                                 'speaker-dates', 'meetings-html'))
    args = parser.parse_args()
    action_map = {'reformat-xml': action_reformat_xml,
                  'speaker-counts': action_speaker_counts,
                  'speaker-dates': action_speaker_dates,
                  'meetings-html': action_meetings_html}
    action_map[args.action](args)


if __name__ == '__main__':
    main()
