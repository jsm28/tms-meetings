#! /usr/bin/python3

import argparse
import collections
import datetime
import html
import re
import xml.etree.ElementTree


nbsp = '\u00a0'
Delta = '\u0394'
pi = '\u03c0'
ndash = '\u2013'
mdash = '\u2014'
rsquo = '\u2019'
ldquo = '\u201c'
rdquo = '\u201d'
hellip = '\u2026'
joint_societies = ('Adams Society', 'Magpie and Stump',
                   'Mathematics Research Students'+rsquo+' Tea Club',
                   'New Pythagoreans', 'Trinity College Music Society',
                   'Trinity College Natural Sciences Society',
                   'Trinity College Science Society')
# Titles are expected to come from this list, in order.  The text list
# used full stops after every abbreviation; for the XML list, the
# common British convention is used where such full stops are not used
# for abbreviations ending with the last letter of the word
# abbreviated.
pers_titles_text = ('Prof. ', 'Rev. ', 'Dr. ', 'Hon. ', 'Col. ', 'Sir ',
                    'Lord ', 'Mr. ', 'Mrs. ', 'Ms. ', 'Miss ')
pers_titles_text_adj = { 'Dr. ': 'Dr ', 'Mr. ': 'Mr ', 'Mrs. ': 'Mrs ',
                         'Ms. ': 'Ms ' }
pers_titles = ('Prof. ', 'Rev. ', 'Dr ', 'Hon. ', 'Col. ', 'Sir ',
               'Lord ', 'Mr ', 'Mrs ', 'Ms ', 'Miss ')
roles = ('proponent', 'opponent', 'author', 'producer')
meeting_types = ('talk', 'talks', 'sporting event', 'dinner', 'debate',
                 'inaugural meeting', 'film night', 'panel discussion',
                 'opera', 'photograph', 'recreational', 'visit',
                 'general meeting', 'business meeting', 'discussion')
meeting_flags = ('non-election business', 'election of officers',
                 'televised')
venues = ('',
          'Adrian House Seminar Room',
          'the College Bar (Q1 Great Court, 1958'+ndash+'1998)',
          'Blue Boar Common Room',
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
          'Wolfson Party Room')
venues_re = ('.* Blue Boar Court',
             'Room .*, 4A Bridge Street',
             '.* Bishop'+rsquo+'s Hostel',
             '.* Great Court',
             '.* Whewell'+rsquo+'s Court',
             '.* New Court',
             r'Lecture Room .* \(I Great Court\)',
             'Centre for Mathematical Sciences MR.*',
             '.* Nevile'+rsquo+'s Court')


def get_title(name, tlist, tlist_adj):
    """Separate a person's title from their name following."""
    title = ''
    for t in tlist:
        if name.startswith(t):
            tx = t
            if t in tlist_adj:
                tx = tlist_adj[t]
            title += tx
            name = name[len(t):]
    title = title.rstrip()
    return (title, name)


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
        ctitle, cname = get_title(title+' ', pers_titles, {})
        if ctitle != title:
            raise ValueError('unexpected title: %s' % title)
        self.title = title
        self.first = first
        self.last = last
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

    def html_text(self):
        """HTML text for a Speaker object in the list of meetings."""
        text = '%s %s %s' % (self.title, self.first, self.last)
        text = text.replace(' ', nbsp)
        if self.role:
            text = '%s (%s)' % (text, self.role)
        return html.escape(text)


class SubMeeting(object):
    """A meeting title or description with zero or more speakers."""

    def __init__(self, desc, title, note, speakers):
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
        self.desc = desc
        self.title = title
        self.note = note
        self.speakers = speakers

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
        return '    <sub>\n%s\n    </sub>' % '\n'.join(s)

    def html_text(self):
        """HTML text for a SubMeeting object in the list of meetings."""
        stext = ' and '.join([s.html_text() for s in self.speakers])
        if self.title:
            dtext = ldquo+self.title+rdquo
        else:
            dtext = self.desc
        if self.note:
            dtext = '%s (%s)' % (dtext, self.note)
        dtext = html.escape(dtext)
        if stext:
            return '%s, %s' % (stext, dtext)
        else:
            return dtext


class Meeting(object):
    """The complete record for a meeting."""

    def __init__(self, number, date, type, flags, joint, sub, venue,
                 attendance, volume, page):
        """Initialize a Meeting object."""
        self.number = number
        if (date != ''
            and not re.fullmatch(r'[1-9][0-9]{3}-[01?][0-9?]-[0123?][0-9?]',
                                 date)):
            raise ValueError('bad date: %s' % date)
        self.date = date
        if type not in meeting_types:
            raise ValueError('bad meeting type: %s' % type)
        self.type = type
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

    def html_text(self):
        """HTML text for a Meeting object in the list of meetings."""
        if self.date == '':
            datetext = '(unknown date)'
        else:
            year = self.date[0:4]
            month = self.date[5:7]
            months = { '01': 'January',
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
                       '??': '??' }
            month = months[month]
            day = self.date[8:]
            day = day.lstrip('0')
            datetext = '%s %s %s' % (day, month, year)
        sub_text_list = [s.html_text() for s in self.sub]
        if len(self.sub) > 1:
            maintext = ('%s:\n<ul>\n%s\n</ul>\n'
                        % (html.escape(datetext),
                           '\n'.join(['<li>%s.</li>' % s
                                      for s in sub_text_list])))
        else:
            maintext = '%s: %s.<br>\n' % (html.escape(datetext),
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

    def html_text(self):
        """HTML text for a Note object in the list of meetings."""
        return '<p>(%s)</p>' % html.escape(self.text)


def convert_text(text):
    """Convert text (e.g. talk title) from list of meetings to full
    Unicode form."""
    if text is None:
        return text
    text = text.replace("'", rsquo)
    text = text.replace('...', hellip)
    text = text.replace(r'\pi', pi)
    text = text.replace(r'\Delta', Delta)
    text = text.replace(' - ', mdash)
    while '"' in text:
        text = text.replace('"', ldquo, 1)
        text = text.replace('"', rdquo, 1)
    text = re.sub(r'([0-9])-([0-9])', r'\1'+ndash+r'\2', text)
    text = re.sub(r'([0-9])-\Z', r'\1'+ndash, text)
    return text


def unconvert_text(text):
    """Convert text (e.g. talk title) from list of meetings to form in
    fixed-format text file."""
    if text is None:
        return text
    text = text.replace(rsquo, "'")
    text = text.replace(hellip, '...')
    text = text.replace(pi, r'\pi')
    text = text.replace(Delta, r'\Delta')
    text = text.replace(mdash, ' - ')
    text = text.replace(ldquo, '"')
    text = text.replace(rdquo, '"')
    text = text.replace(ndash, '-')
    return text


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
            type = entry.find('type').text
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
                sub.append(SubMeeting(desc, title, note, speakers))
            if type == 'talk' and len(sub) != 1:
                raise ValueError('meeting %s (talk) has multiple talks',
                                 number)
            if type == 'talks' and len(sub) <= 1:
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
            meeting_list.append(Meeting(number, date, type, flags, joint,
                                        sub, venue, attendance, volume, page))
        elif entry.tag == 'note':
            meeting_list.append(Note(entry.text))
        else:
            raise ValueError('unexpected tag: %s' % entry.tag)
    return meeting_list


volumes = { 'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
            'XI': '11', 'XII': '12' }
format_hdr = 'mmmxx yyyy-mm-dd fff joint speaker                          title                                                                                                   venue ppp aud'
volume_hdr = 'VOLUME '
joint_map = { '': (),
              'Adams': ('Adams Society',),
              'M&S': ('Magpie and Stump',),
              'A/M&S': ('Adams Society', 'Magpie and Stump'),
              'MRSTC': ('Mathematics Research Students'+rsquo+' Tea Club',),
              'NP': ('New Pythagoreans',),
              'TCMS': ('Trinity College Music Society',),
              'TCNSS': ('Trinity College Natural Sciences Society',),
              'TCSS': ('Trinity College Science Society',) }
role_map = { 'prop': 'proponent',
             'opp': 'opponent',
             'author': 'author',
             'producer': 'producer' }
type_map = { 'c': 'sporting event',
             'd': 'dinner',
             'f': 'debate',
             'i': 'inaugural meeting',
             'm': 'film night',
             'n': 'panel discussion',
             'o': 'opera',
             'p': 'photograph',
             'r': 'recreational',
             'v': 'visit' }
flag_map = { 'b': 'non-election business',
             'e': 'election of officers',
             't': 'televised' }
venue_map = { 'AHSR': 'Adrian House Seminar Room',
              'BBCR': 'Blue Boar Common Room',
              'BHPR': 'Butler House Party Room',
              'CAI': 'Caius College',
              'CAM': 'river Cam',
              'CHR': 'Christ'+rsquo+'s College',
              'DAMTP': 'DAMTP',
              'EMM': 'Emmanuel College',
              'Hall': 'Hall',
              'JCR': 'Junior Combination Room',
              'JP': 'Junior Parlour',
              'LRT': 'Lecture-Room Theatre (I Great Court)',
              'ML': 'Master'+rsquo+'s Lodge',
              'OCR': 'Old Combination Room',
              'OF': 'Old Field',
              'OK': 'Old Kitchens',
              'PSR': 'Private Supply Room',
              'SJC': 'St John'+rsquo+'s College',
              'WLT': 'Winstanley Lecture Theatre',
              'WPR': 'Wolfson Party Room' }
venue_map_suffix = collections.OrderedDict(
    (('BB', '%s Blue Boar Court'),
     ('BS', 'Room %s, 4A Bridge Street'),
     ('B', '%s Bishop'+rsquo+'s Hostel'),
     ('G', '%s Great Court'),
     ('H', '%s Whewell'+rsquo+'s Court'),
     ('K', '%s New Court'),
     ('LR', 'Lecture Room %s (I Great Court)'),
     ('MR', 'Centre for Mathematical Sciences MR%s'),
     ('N', '%s Nevile'+rsquo+'s Court')))
venue_bar_text = 'Q1 Great Court'
venue_bar = 'the College Bar (Q1 Great Court, 1958'+ndash+'1998)'
def meetings_from_text(name):
    """Read the list of meetings from a fixed-format text file."""
    cur_volume = None
    meeting_list = []
    cur_meeting = None
    with open(name, 'r', encoding='iso-8859-1') as f:
        for line in f:
            line = line.rstrip()
            # Ignore blank lines, and underlining of volume numbers.
            if line.rstrip('-') == '':
                if line != '' and cur_meeting is not None:
                    raise ValueError('unexpected underlining')
                continue
            # Ignore headers describing the format.
            if line == format_hdr:
                if cur_meeting is not None:
                    raise ValueError('unexpected format header')
                continue
            if line.startswith(volume_hdr):
                cur_volume = volumes[line[len(volume_hdr):]]
                cur_meeting = None
                continue
            if line.startswith('('):
                if not line.endswith(')'):
                    raise ValueError('bad note line: %s' % line)
                line = line[1:-1]
                cur_meeting = None
                meeting_list.append(Note(convert_text(line)))
                continue
            # Meeting or meeting continuation line.
            line = line.ljust(178)
            if len(line) != 178:
                raise ValueError('line too long: %s' % line)
            number = line[0:5].strip()
            sp1 = line[5]
            date = line[6:16].strip()
            sp2 = line[16]
            flags = line[17:20].rstrip()
            sp3 = line[20]
            joint = line[21:26].lstrip()
            sp4 = line[26]
            speaker = line[27:59].rstrip()
            sp5 = line[59]
            desc = line[60:163].rstrip()
            sp6 = line[163]
            venue = line[164:169].rstrip()
            sp7 = line[169]
            page = line[170:173].lstrip()
            sp8 = line[173]
            attendance = line[174:].strip()
            if speaker == 'unminuted' and desc == '':
                speaker = ''
                desc = '(unminuted)'
            if (sp1 != ' ' or sp2 != ' ' or sp3 != ' ' or sp4 != ' '
                or sp5 != ' ' or sp6 != ' ' or sp7 != ' ' or sp8 != ' '):
                raise ValueError('missing expected space in line: %s' % line)
            if speaker.startswith(' '):
                raise ValueError('speaker starts with space: %s' % line)
            if desc.startswith(' '):
                raise ValueError('description starts with space: %s' % line)
            if number == '' and date == '':
                # Continuation line.
                continuation = True
                if flags or joint or venue or page or attendance:
                    raise ValueError('bad continuation line: %s' % line)
            else:
                # Start of the lines for a new meeting.
                continuation = False
                type = ''
                flags_list = []
                for f in flags:
                    if f in type_map:
                        if type != '':
                            raise ValueError('multiple meeting types: %s'
                                             % line)
                        type = type_map[f]
                    elif f in flag_map:
                        flags_list.append(flag_map[f])
                    else:
                        raise ValueError('unknown flag: %s' % line)
                if type == '':
                    if (speaker
                        or desc == '(no speaker present)'
                        or desc == '(unminuted)'):
                        type = 'talk'
                    elif 'General Meeting' in desc:
                        type = 'general meeting'
                    elif 'Business Meeting' in desc:
                        type = 'business meeting'
                    elif desc.startswith('Discussion'):
                        type = 'discussion'
                    else:
                        raise ValueError('unknown meeting type: %s' % line)
                if venue != '':
                    if venue in venue_map:
                        venue = venue_map[venue]
                    else:
                        venue_converted = False
                        for v in venue_map_suffix:
                            if venue.startswith(v):
                                venue_suffix = venue[len(v):]
                                venue = venue_map_suffix[v] % venue_suffix
                                venue_converted = True
                                break
                        if not venue_converted:
                            raise ValueError('unknown venue: %s' % line)
                        if venue == venue_bar_text and date == '1979-04-23':
                            venue = venue_bar
                        if venue == 'Lecture Room  (I Great Court)':
                            venue = 'Lecture Rooms (I Great Court)'
                if page == '---' or page == '':
                    page = '-'
                if page == '???':
                    page = '?'
                if attendance == '??':
                    attendance = '?'
                cur_meeting = Meeting(number, date, type, flags_list,
                                      joint_map[joint], [], venue, attendance,
                                      cur_volume, page)
                meeting_list.append(cur_meeting)
            if speaker:
                speaker_title, speaker_name = get_title(speaker,
                                                        pers_titles_text,
                                                        pers_titles_text_adj)
                if not speaker_title:
                    raise ValueError('missing speaker title: %s' % line)
                if speaker_name.endswith(')'):
                    m = re.fullmatch(r'(.+) \(([^()]*)\)', speaker_name)
                    if not m:
                        raise ValueError('bad speaker: %s' % line)
                    speaker_name = m.group(1)
                    speaker_role = role_map[m.group(2)]
                else:
                    speaker_role = None
                m = re.fullmatch(r'(.*\.) ([^.]*)', speaker_name)
                if not m:
                    raise ValueError('bad speaker: %s' % line)
                speaker_first = m.group(1)
                # Insert spaces between initials.
                speaker_first = re.sub(r'([A-Z])\.(?=[A-Z])', r'\1. ',
                                       speaker_first)
                speaker_last = m.group(2)
                speaker_obj = Speaker(speaker_title, speaker_first,
                                      speaker_last, speaker_role)
            else:
                speaker_obj = None
            if desc.endswith(' ..."'):
                # Title too long for fixed-width format, full title in
                # .title file.
                titlefile = '%s.title' % cur_meeting.number
                with open(titlefile, 'r', encoding='iso-8859-1') as ftitle:
                    titlelines = ftitle.readlines()
                if len(titlelines) != 1:
                    raise ValueError('bad number of lines in %s' % titlefile)
                tline = titlelines[0].strip()
                sdesc = desc[1:-5]
                if not tline.startswith(sdesc):
                    raise ValueError('long title mismatch: %s' % line)
                desc = '"%s"' % tline
            if desc.endswith(')') and not desc.startswith('('):
                m = re.fullmatch(r'(.+) \(([^()]*)\)', desc)
                if not m:
                    raise ValueError('bad note: %s' % line)
                desc = m.group(1)
                note = m.group(2)
            else:
                note = None
            if desc.startswith('"') and desc.endswith('"'):
                title = desc[1:-1]
                desc = None
            else:
                title = None
            desc = convert_text(desc)
            title = convert_text(title)
            note = convert_text(note)
            if desc or title:
                # New description/title (and so new speaker if any).
                if speaker_obj:
                    speaker_list = [speaker_obj]
                else:
                    speaker_list = []
                cur_meeting.sub.append(SubMeeting(desc, title, note,
                                                  speaker_list))
                if cur_meeting.type == 'talk' and len(cur_meeting.sub) > 1:
                    cur_meeting.type = 'talks'
            else:
                # New speaker for the previous title.
                if not speaker_obj:
                    raise ValueError('missing speaker name: %s' % line)
                cur_meeting.sub[-1].speakers.append(speaker_obj)
    return meeting_list


def meetings_to_xml(meeting_list):
    """Return the canonical XML text of the list of meetings."""
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<meetings>\n'
            '%s\n'
            '</meetings>\n'
            % '\n'.join([m.xml_text() for m in meeting_list]))


def meetings_to_text(meeting_list):
    """Return the legacy text form of the list of meetings.

    This is for one-off validation that the conversion process from
    text to XML does not lose information.  Thus, it is not necessary
    for the results to be byte-identical to the original text file, or
    to be fully validly formatted suitably for reading back in, just
    similar enough for comparison.  Specifically, there are
    differences in how some unminuted meetings are reflected in the
    text file, and this output does not truncate too-long meeting
    titles (so the output for those meetings is not actually valid
    input for the text-to-XML conversion).

    """
    lines = []
    cur_year = 0
    cur_volume = '0'
    for m in meeting_list:
        done_newline = False
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
            done_newline = True
            if cur_year != 0:
                lines.append('')
            cur_year = year
        elif year != cur_year:
            raise ValueError('year going backwards')
        if isinstance(m, Meeting) and m.volume != cur_volume:
            if not done_newline:
                lines.append('')
                done_newline = True
            if cur_volume != '0':
                lines.append('')
            cur_volume = m.volume
            vol_roman = ''
            for k in volumes:
                if volumes[k] == m.volume:
                    vol_roman = k
                    break
            vol_txt = volume_hdr + vol_roman
            lines.append(vol_txt)
            lines.append('-' * len(vol_txt))
            lines.append(format_hdr)
        if isinstance(m, Note):
            lines.append('(%s)' % unconvert_text(m.text))
            continue
        num = re.fullmatch(r'([0-9]+)(.*)', m.number)
        if num:
            num_main = num.group(1)
            num_extra = num.group(2)
        else:
            num_main = ''
            num_extra = ''
        flags = ''
        for t in type_map:
            if m.type == type_map[t]:
                flags += t
                break
        for f in flag_map:
            if flag_map[f] in m.flags:
                flags += f
        flags = ''.join(sorted(flags))
        joint = ''
        for j in joint_map:
            if tuple(m.joint) == joint_map[j]:
                joint = j
                break
        sub = []
        for s in m.sub:
            if s.desc:
                desc = s.desc
            else:
                desc = '"%s"' % s.title
            if s.note:
                desc = '%s (%s)' % (desc, s.note)
            desc = unconvert_text(desc)
            if s.speakers:
                speakers = []
                for sp in s.speakers:
                    title = sp.title + ' '
                    for k in pers_titles_text_adj:
                        title = title.replace(pers_titles_text_adj[k], k)
                    first = sp.first
                    first = first.replace('. ', '.')
                    first = first.replace('.St', '. St')
                    first = first.replace('.v', '. v')
                    sp_text = '%s%s %s' % (title, first, sp.last)
                    if sp.role:
                        role = sp.role
                        for k in role_map:
                            if role == role_map[k]:
                                role = k
                        sp_text += ' (%s)' % role
                    speakers.append(sp_text)
            else:
                speakers = ['']
            sub.append((speakers[0], desc))
            for sp in speakers[1:]:
                sub.append((sp, ''))
        venue = ''
        if m.venue:
            mvenue = m.venue
            if mvenue == venue_bar:
                mvenue = venue_bar_text
            if mvenue == 'Lecture Rooms (I Great Court)':
                mvenue = 'Lecture Room  (I Great Court)'
            for k in venue_map:
                if mvenue == venue_map[k]:
                    venue = k
                    break
            if not venue:
                for k in venue_map_suffix:
                    name_re = venue_map_suffix[k]
                    name_re = name_re.replace('(', r'\(')
                    name_re = name_re.replace(')', r'\)')
                    name_re = name_re.replace('%s', '(.*)')
                    vmatch = re.fullmatch(name_re, mvenue)
                    if vmatch:
                        venue = k + vmatch.group(1)
                        break
            if not venue:
                raise ValueError('could not convert venue: %s' % mvenue)
        page = m.page
        if page == '-':
            page = '---'
        if page == '?':
            page = '???'
        if m.attendance:
            attendance = m.attendance
            if attendance == '?':
                attendance = ' ??'
            att_match = re.fullmatch('([0-9]+)(.*)', attendance)
            if att_match:
                attendance = '%3s%s' % (att_match.group(1), att_match.group(2))
        else:
            attendance = ''
        lines.append(('%3s%-2s %-10s %-3s %5s %-32s %-103s %-5s %3s %s'
                      % (num_main, num_extra, m.date, flags, joint, sub[0][0],
                         sub[0][1], venue, page, attendance)).rstrip())
        for s in sub[1:]:
            lines.append(('%27s%-32s %-133s' % ('', s[0], s[1])).rstrip())
    return '\n'.join(lines) + '\n'


def action_text_to_xml(args):
    """Convert the text list of meetings to XML."""
    mlist = meetings_from_text('meetings.txt')
    xml_text = meetings_to_xml(mlist)
    with open('meetings.xml', 'w', encoding='utf-8') as f:
        f.write(xml_text)


def action_reformat_xml(args):
    """Read the XML list of meetings and write it out again."""
    mlist = meetings_from_xml('meetings.xml')
    xml_text = meetings_to_xml(mlist)
    with open('meetings-new.xml', 'w', encoding='utf-8') as f:
        f.write(xml_text)


def action_speaker_counts(args):
    """Count the number of talks by each speaker."""
    meeting_list = meetings_from_xml('meetings.xml')
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
                name = '%s, %s' % (sp.last, sp.first)
                if name not in counts:
                    counts[name] = 0
                counts[name] += 1
    sorted_speakers = sorted(counts.keys(), key=lambda s:(counts[s], s))
    sorted_list = ['%7d %s' % (counts[s], s) for s in sorted_speakers]
    sorted_text = '\n'.join(sorted_list) + '\n'
    with open('speaker-counts.txt', 'w', encoding='utf-8') as f:
        f.write(sorted_text)


def action_speaker_dates(args):
    """List speakers by the range of dates over which they have spoken."""
    meeting_list = meetings_from_xml('meetings.xml')
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
                name = '%s, %s' % (sp.last, sp.first)
                if name in dates:
                    details = (dates[name][0], dates[name][1], m.date,
                               (date - dates[name][1]).days)
                else:
                    details = (m.date, date, m.date, 0)
                dates[name] = details
    sorted_speakers = sorted(dates.keys(), key=lambda s:(dates[s][3], s))
    sorted_list = [('%7d %-25s %s - %s'
                    % (dates[s][3], s, dates[s][0], dates[s][2]))
                   for s in sorted_speakers]
    sorted_text = '\n'.join(sorted_list) + '\n'
    with open('speaker-dates.txt', 'w', encoding='utf-8') as f:
        f.write(sorted_text)


def action_meetings_html(args):
    """Generate an HTML version of the list of meetings."""
    meeting_list = meetings_from_xml('meetings.xml')
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
        cur_text += '\n' + m.html_text()
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


def action_meetings_text(args):
    """Read the XML list of meetings and write it out in legacy text form."""
    mlist = meetings_from_xml('meetings.xml')
    new_text = meetings_to_text(mlist)
    with open('meetings-new.txt', 'w', encoding='iso-8859-1') as f:
        f.write(new_text)


def main():
    """Main program."""
    parser = argparse.ArgumentParser(description='Process list of meetings')
    parser.add_argument('--exclude',
                        action='append',
                        help='Types of meetings to ignore for statistics')
    parser.add_argument('action',
                        help='What to do',
                        choices=('text-to-xml', 'reformat-xml',
                                 'speaker-counts', 'speaker-dates',
                                 'meetings-html', 'meetings-text'))
    args = parser.parse_args()
    action_map = { 'text-to-xml': action_text_to_xml,
                   'reformat-xml': action_reformat_xml,
                   'speaker-counts': action_speaker_counts,
                   'speaker-dates': action_speaker_dates,
                   'meetings-html': action_meetings_html,
                   'meetings-text': action_meetings_text }
    action_map[args.action](args)


if __name__ == '__main__':
    main()
