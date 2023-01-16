DEVELOPER_KEY = "AIzaSyCTpkDl2CtJDujEGckqw7wjwa2fU6nrqEg"  # API Key 
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

CHANNEL_IDS = ["UCupvZG-5ko_eiXAupbDfxWw", "UCaXkIU1QidjPwiAYu6GcHjg", "UCXIJgqnII2ZOINSWNOGFThA"] # Fox News channel ID

VIDEO_COLS = ["videoId", "title", "publishedAt",
              "channelId", "channelName", "views", "likes", "num_comments"]
COMMENT_COLS = ["comment_id", "videoId", "textOriginal", "authorDisplayName",
                "authorChannelId", "likeCount", "publishedAt"]
VIDEOS_CSV = "videos.csv"
COMMENTS_CSV = "comments.csv"
W2V_SIZE = 64
