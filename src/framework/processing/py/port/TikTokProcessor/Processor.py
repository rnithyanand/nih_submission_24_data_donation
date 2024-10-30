import json
import zipfile
import itertools
from contextlib import suppress
from datetime import datetime, timedelta
from collections import defaultdict


class TikTokDataProcessing:

    def __init__(self, filepath):
        self.posts = None
        self.likes = None
        self.chats = None
        self.comments = None
        self.shares = None
        self.browsing = None
        self.username = None
        self.product_browsing = None
        self.activity_timeline = None
        self.filepath = filepath

    def extract_data(self):
        if self.filepath.endswith('.zip'):
            with zipfile.ZipFile(self.filepath, 'r') as zip:
                for filename in zip.namelist():
                    if filename.endswith('.json'):
                        with zip.open(filename) as json_file:
                            with suppress(IOError, json.JSONDecodeError):
                                self.data = json.load(json_file)
        else:
            with open(self.filepath, 'rb') as json_file:
                with suppress(IOError, json.JSONDecodeError):
                    self.data = json.load(json_file)
        self.get_all_data()

    def get_all_data(self):
        self.username = self.get_username()
        self.browsing = self.get_browsing_data()
        self.shares = self.get_sharing_data()
        self.comments = self.get_comment_data()
        self.chats = self.get_chat_data()
        self.likes = self.get_like_data()
        self.posts = self.get_post_data()
        self.product_browsing = self.get_product_browsing_data()
        return

    def print_summary_data(self):
        print("Username: %s " % self.username)
        print("Number of videos watched: %d" % len(self.browsing))
        print("Number of videos shared: %d" % len(self.shares))
        print("Number of comments made: %d" % len(self.comments))
        print("Number of DMs sent and received: %d" % len(self.chats))
        print("Number of videos liked: %d" % len(self.likes))
        print("Number of videos posted: %d" % len(self.posts))
        print("Number of products browsed: %d" % len(self.product_browsing))

    @staticmethod
    def update_timeline(date_str, activity, timeline):
        date_hour = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:00:00")
        timeline[date_hour][activity] += 1
        return timeline

    def get_activity_timeline(self):
        timeline = defaultdict(lambda: {"browsed": 0, "shared": 0, "commented": 0, "liked": 0, "posted": 0, "dmed": 0,
                                        "product_browsed": 0})

        one_year_ago = datetime.now() - timedelta(days=365)

        def process_activity(activity_list, activity_type):
            for item in activity_list:
                date = datetime.strptime(item["Date"], "%Y-%m-%d %H:%M:%S")
                if date >= one_year_ago:
                    date_hour = date.strftime("%Y-%m-%d %H:00:00")
                    timeline[date_hour][activity_type] += 1

        process_activity(self.browsing, 'browsed')
        process_activity(self.shares, 'shared')
        process_activity(self.comments, 'commented')
        process_activity(self.likes, 'liked')
        process_activity(self.posts, 'posted')
        process_activity(self.chats, 'dmed')

        for product in self.product_browsing:
            date = datetime.strptime(product["browsing_date"], "%Y-%m-%d %H:%M:%S")
            if date >= one_year_ago:
                date_hour = date.strftime("%Y-%m-%d %H:00:00")
                timeline[date_hour]['product_browsed'] += 1

        self.activity_timeline = timeline
        for date in self.activity_timeline:
            self.activity_timeline[date]['n_events'] = sum([self.activity_timeline[date][i] for i in ['browsed',
                                                                                                      'shared',
                                                                                                      'commented',
                                                                                                      'liked',
                                                                                                      'posted',
                                                                                                      'dmed',
                                                                                                      'product_browsed']])

    def get_username(self):
        key_path = ["Profile", "Profile Information", "ProfileMap", "userName"]
        return self.get_items(self.data, failed_return_value="Could Not Be Extracted", key_path=key_path)

    def get_browsing_data(self):
        key_path = ["Activity", "Video Browsing History", "VideoList"]
        return self.get_items(self.data, failed_return_value=[], key_path=key_path)

    def get_sharing_data(self):
        key_path = ["Activity", "Share History", "ShareHistoryList"]
        return self.get_items(self.data, failed_return_value=[], key_path=key_path)

    def get_like_data(self):
        key_path = ["Activity", "Favorite Videos", "FavoriteVideoList"]
        return self.get_items(self.data, failed_return_value=[], key_path=key_path)

    def get_comment_data(self):
        key_path = ["Comment", "Comments", "CommentsList"]
        return self.get_items(self.data, failed_return_value=[], key_path=key_path)

    def get_post_data(self):
        key_path = ["Video", "Videos", "VideoList"]
        return self.get_items(self.data, failed_return_value=[], key_path=key_path)

    def get_chat_data(self):
        key_path = ["Direct Messages", "Chat History", "ChatHistory"]
        chats = self.get_items(self.data, failed_return_value={}, key_path=key_path)
        return list(itertools.chain(*chats.values()))

    def get_product_browsing_data(self):
        key_path = ["TikTok Shopping", "Product Browsing History", "ProductBrowsingHistories"]
        return self.get_items(self.data, failed_return_value=[], key_path=key_path)

    @staticmethod
    def get_items(data_dict, failed_return_value, key_path):
        for k in key_path:
            data_dict = data_dict.get(k, None)
            if data_dict is None:
                return failed_return_value
        return data_dict

