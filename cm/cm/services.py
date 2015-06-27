from collections import defaultdict

import os
from django import db
import re

from nltk.stem.snowball import EnglishStemmer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

conn = db.connections['default']
cursor = conn.cursor()

def chunks(l, size):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), size):
        yield l[i:i+size]

def calculate_app_weights():
    pass


def _do_calculate_tag(base_tag_apps, tag_apps):
    same_app_ids = list(set(base_tag_apps.keys()) & set(tag_apps.keys()))
    same_app_count = len(same_app_ids)
    base_tag_apps_count = len(base_tag_apps)
    tag_apps_count = len(tag_apps)

    base_tag_rate = float(same_app_count) / base_tag_apps_count
    tag_rate = float(same_app_count) / tag_apps_count
    similarity = (base_tag_rate + tag_rate) / 2
    return round(similarity, 5)


def calculate_tag_similarity():
    # Get all tags
    cursor.execute('SELECT DISTINCT(tag) FROM tag_app_rel;')
    tags = [re.sub(r"[^a-zA-Z0-9]+","",r[0]) for r in cursor]

    all_tag_data = defaultdict(dict)
    for tag_batch in chunks(tags, 1000):
        cursor.execute(
            cursor.mogrify(
                'SELECT tag, app_id, times FROM tag_app_rel WHERE tag IN %s;', (tuple(tag_batch), )
            )
        )
        for r in cursor:
            all_tag_data[r[0]][r[1]] = r[2]
    all_tags = all_tag_data.keys()

    # Calculate similarity for each two tags
    similarity_data = []
    for i, base_tag in enumerate(all_tags):
        print '**%s, %s' % (i, base_tag)
        for j, tag in enumerate(all_tags[i+1:]):
            base_tag_data = all_tag_data[base_tag]
            tag_data = all_tag_data[tag]
            similarity = _do_calculate_tag(base_tag_data, tag_data)
            if similarity > 0.0:
                similarity_data.append([base_tag, tag, similarity])

    import pdb;pdb.set_trace()
    # Insert similarity
    cursor.execute('Truncate table tag_similarity;')
    db.transaction.commit_unless_managed(using='default')
    insert_sql = 'INSERT INTO tag_similarity (base_tag, tag, similarity) VALUES (%s, %s, %s);'
    for base, tag, similarity in similarity_data:
        cursor.execute(insert_sql, (base, tag, similarity))

    db.transaction.commit_unless_managed(using='default')


def normalize_tags():
    cursor.execute('SELECT app_id, tag, times FROM tag_app_rel;')
    all_tag_data = defaultdict(dict)
    for r in cursor:
        all_tag_data[r[0]][r[1]] = r[2]

    stemmer = EnglishStemmer()
    for app_id, tag_to_times in all_tag_data.iteritems():
        normalized_app_tag_dict = defaultdict(int)
        for tag, times in tag_to_times.iteritems():
            normalized_app_tag_dict[stemmer.stem(tag)] += times
        for tag, times in normalized_app_tag_dict.iteritems():
            cursor.execute('INSERT INTO tag_app_relation (app_id, tag, times) VALUES (%s, %s, %s)', (app_id, tag, times))


if __name__ == "__main__":
    calculate_tag_similarity()