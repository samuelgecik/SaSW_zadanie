import os
import string
import pandas as pd
import datasets
import consts
from nltk.tokenize import sent_tokenize, word_tokenize
import gensim
from gensim.models import Word2Vec
import numpy as np
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification


trans = str.maketrans("", "", string.punctuation)  # to eliminate punctuation


def search_comments(df, query):
    """
    Search comments database for query and print matching comments
    :param df: DataFrame containing comments to search
    :param query: string to search for
    :return: None
    """
    subset = df[df["textOriginal"].str.contains(query, case=False)]
    subset = subset.sample(min(50, len(subset.index)))
    comments = subset["textOriginal"]
    for c in list(comments):
        print("{}".format(c))
        print("*" * 60)


def search_histogram(df, query):
    """
    Search comments database for query and show histogram of matching comments,
    color-coded by channel
    :param df: DataFrame containing comments to search
    :param query: string to search for
    :return: None
    """
    fig = px.histogram(
        df[df["textOriginal"].str.contains(query, case=False)],
        "publishedAt",
        color="channelName",
    )
    fig.show()


def train_word2vec(df, comments_file, model_file):
    """
    train and save a word2vec model based on comments database
    :param df: DataFrame containing comments
    :param comments_file: txt file to save comments to
    :param model_file: file to save the word2vec model to for later use
    :return: the word2vec model
    """
    # save comments in text file (useful for inspection)
    with open(comments_file, "w") as f:
        for entry in df["textOriginal"]:
            f.write(entry + "\n")

    # read in comments, tokenize, and train word2vec model
    with open(comments_file) as f:
        s = f.read().lower()
    data = []
    for i in sent_tokenize(s):
        temp = []
        for j in word_tokenize(i):
            temp.append(j)
        data.append(temp)
    model = gensim.models.Word2Vec(
        data, min_count=1, vector_size=consts.W2V_SIZE, window=5
    )
    model.save(model_file)
    return model


def plot_comments(df):
    """
    Plot comments using word2vec and t-sne. comments are vectorized as the average of their individual
    word vectors, weighted by tf-idf
    :param df: DataFrame containing comments to plot
    :return: None
    """
    # tfidf conversion
    with open("all_comments.txt", "w") as f:
        for entry in df["textOriginal"]:
            f.write(entry + "\n")
    with open("all_comments.txt") as f:
        t = f.read().lower().translate(trans).split("\n")
    tfidf = TfidfVectorizer()
    tfidf.fit_transform(t)
    lookup = dict(zip(tfidf.get_feature_names_out(), tfidf.idf_))

    # apply word2vec and perform weighted average
    assert os.path.exists("all_comments.model")
    model = Word2Vec.load("all_comments.model").wv
    comment_vectors = []
    for comment in list(df["textOriginal"]):
        embeddings = []
        weights = []
        for word in comment.lower().translate(trans).split():
            if word in model and word in lookup:
                embeddings.append(model[word])
                weights.append(lookup[word])
        if len(embeddings) == 0:
            print("oops: [{}]".format(comment))
            comment_vectors.append(np.array([0.0] * consts.W2V_SIZE))
        else:
            comment_vectors.append(np.average(embeddings, axis=0, weights=weights))

    # apply t-SNE
    comment_vectors = np.array(comment_vectors)
    m, k = comment_vectors.shape
    tsne_model_2d = TSNE(
        perplexity=15, n_components=2, init="pca", n_iter=3500, random_state=32
    )
    embeddings_2d = np.array(tsne_model_2d.fit_transform(comment_vectors.reshape(m, k)))

    # scatter plot
    df["tsne_x"] = embeddings_2d[:, 0]
    df["tsne_y"] = embeddings_2d[:, 1]
    fig = px.scatter(
        df,
        x="tsne_x",
        y="tsne_y",
        color="channelName",
        hover_data=["textOriginal", "likeCount", "authorDisplayName"],
    )
    fig.show()


def clusters(keys, n, model):
    """
    Plot clusters of n most similar words for given keys
    :param keys: a list of words to use as the foci for the clusters
    :param n: number of similar words to include in each cluster
    :return: None
    """
    # find most similar words and their embeddings (vectors)
    embedding_clusters = []
    word_clusters = []
    for word in keys:
        embeddings = []
        words = []
        for similar_word, _ in model.most_similar(word, topn=n):
            words.append(similar_word)
            embeddings.append(model[similar_word])
        embedding_clusters.append(embeddings)
        word_clusters.append(words)

    # apply t-SNE and plot
    embedding_clusters = np.array(embedding_clusters)
    n, m, k = embedding_clusters.shape
    tsne_model = TSNE(
        perplexity=15, n_components=2, init="pca", n_iter=3500, random_state=32
    )
    embeddings = np.array(
        tsne_model.fit_transform(embedding_clusters.reshape(n * m, k))
    ).reshape((n, m, 2))
    fig = go.Figure()
    for key, embeddings, words in zip(keys, embeddings, word_clusters):
        fig.add_trace(
            go.Scatter(
                x=embeddings[:, 0],
                y=embeddings[:, 1],
                name=key,
                mode="markers+text",
                text=words,
                textposition="top center",
            )
        )
    fig.show()


# look for most prolific commenter on a given channel and plot their comments over time
def plot_most_prolific(df, channelName=None):
    if channelName:
        df = df[df["channelName"] == channelName]

    # identify and filter for top commenter from each channel
    top_commenters = []
    for channel in df["channelName"].unique():
        # create a dataframe of counts of comments by each user with columns "authorDisplayName", "authorChannelId", "count"
        counts = (
            df[df["channelName"] == channel]
            .groupby(["authorDisplayName", "authorChannelId"])
            .size()
        )
        counts = counts.reset_index(name="count")
        counts = counts.sort_values(by="count", ascending=False, ignore_index=True)

        top_commenter = counts["authorChannelId"][0]
        top_commenters.append(top_commenter)

    # plot comments over time for each top commenter
    for top_commenter in top_commenters:
        df_top = df[df["authorChannelId"] == top_commenter].copy(deep=True)
        df_top["count"] = 1
        df_top["time"] = df_top["publishedAt"].apply(
            lambda x: pd.Timestamp(x)
            .to_pydatetime()
            .replace(
                second=0,
                microsecond=0,
                minute=pd.Timestamp(x).to_pydatetime().minute // 30 * 30,
            )
        )
        df_top = df_top.sort_values(by="publishedAt", ignore_index=True)
        df_top["summ"] = df_top["textOriginal"].apply(lambda x: x[: min(len(x), 50)])
        fig = px.bar(
            df_top,
            x="time",
            y="count",
            color="videoId",
            hover_data=[
                "summ",
                "likeCount",
                "channelName",
                "publishedAt",
                "authorDisplayName",
                "authorChannelId",
            ],
        )
        fig.show()


# get dataframes of top commenters for given channels
def get_top_commenters(df, channelName=None) -> list[pd.DataFrame]:
    if channelName:
        df = df[df["channelName"] == channelName]
    if len(df) == 0:
        raise ValueError("No channel found for given ID.")
    # identify and filter for top commenter from each channel
    dataframes = []
    for channel in df["channelName"].unique():
        # create a dataframe of counts of comments by each user with columns "authorDisplayName", "authorChannelId", "count"
        counts = (
            df[df["channelName"] == channel]
            .groupby(["authorDisplayName", "authorChannelId"])
            .size()
        )
        counts = counts.reset_index(name="count")
        counts = counts.sort_values(by="count", ascending=False, ignore_index=True)
        dataframes.append(counts)
    return dataframes


def get_comments(
    df, channelName=None, authorChannelId=None, top_authors=5
) -> list[pd.DataFrame]:
    top_commenters = get_top_commenters(df, channelName)
    if authorChannelId:
        for top_commenter in top_commenters:
            if authorChannelId in top_commenter["authorChannelId"].values:
                # return dataframe of authorId, authorDisplayName, channelId and comments for given author
                df = df[df["authorChannelId"] == authorChannelId]
                df = df[
                    [
                        "authorChannelId",
                        "authorDisplayName",
                        "channelId",
                        "textOriginal",
                    ]
                ]
                return df
        raise ValueError("No comments found for given author.")

    # get comments for top authors
    dataframes = []
    for top_commenter in top_commenters:
        # take top authors
        top_commenter = top_commenter[:top_authors]
        for authorChannelId in top_commenter["authorChannelId"]:
            # return dataframe of authorId, authorDisplayName, channelId and comments for given author
            comments_df = df[df["authorChannelId"] == authorChannelId].copy(deep=True)
            comments_df = comments_df[
                ["authorChannelId", "authorDisplayName", "channelId", "textOriginal"]
            ]
            dataframes.append(comments_df)
    return dataframes


def get_sentiment(model=None, tokenizer=None, data_list=None):
    model = AutoModelForSequenceClassification.from_pretrained(
        "Ivor22/distilbert-base-uncased-finetuned-sst2"
    )
    tokenizer = AutoTokenizer.from_pretrained(
        "Ivor22/distilbert-base-uncased-finetuned-sst2"
    )
    sentiment_analysis = pipeline(
        "sentiment-analysis", model=model, tokenizer=tokenizer
    )
    return sentiment_analysis(data_list)

def flag_trolls(df, channelName=None, authorChannelId=None, top_authors=5):
    comments = get_comments(df, channelName, authorChannelId, top_authors)
    possible_trolls = []
    for i in range(len(comments)):
        sentiment = get_sentiment(data_list=list(comments[i]["textOriginal"].values))
        positive = len([x for x in sentiment if x['label'] == 'LABEL_1'])
        negative = len([x for x in sentiment if x['label'] == 'LABEL_0'])
        print(f"Channel {i+1} has {negative} negative comments out of {len(comments[i])} total comments")
        if negative > positive:
            print("Channel has been flagged as a possible troll channel")
            print("Channel name: ", comments[i]["authorDisplayName"].values[0])
            print("Number of comments classified as negative: ", negative)
            print("Total number of comments: ", len(comments[i]))
            print("Percentage of negative comments: ", negative/len(comments[i]) * 100, "%")
            possible_trolls.append(comments[i]["authorDisplayName"].values[0])
        print("=============================================================")
    return possible_trolls


# plot comment embeddings for given channels
def experiment_w2v_comments(df):
    if not os.path.exists("all_comments.model"):
        train_word2vec(df, "all_comments.txt", "all_comments.model")
    df = df[df["likeCount"] > 30]  # threshold of likes
    dfs = [
        df[df["channelName"] == "The New York Times"],
        df[df["channelName"] == "MSNBC"],
    ]
    plot_comments(pd.concat(dfs))


# compare what words are considered similar to query words based on different word2vec models
def experiment_clusters():
    # df = df[(df["channelName"] == "Fox News") | (df["channelName"] == "New York Times")]
    # train_word2vec(df, "comments_only.txt", "word2vec.model")
    # models = [Word2Vec.load("comments_fox.model").wv, Word2Vec.load("comments_nyt.model").wv,
    #           Word2Vec.load("comments_msnbc.model").wv]
    models = [
        train_word2vec(
            df[df["channelName"] == "CNN"], "comments_cnn.txt", "comments_cnn.model"
        ).wv,
        train_word2vec(
            df[df["channelName"] == "MSNBC"],
            "comments_msnbc.txt",
            "comments_msnbc.model",
        ).wv,
    ]
    for model in models:
        clusters(["gop", "trump"], 20, model)


# find top num repeat comments and save them to csv file, useful to look for bots
def experiment_repeats(df, num):
    df["count"] = 1
    agg_dict = {
        "likeCount": "sum",
        "count": sum,
        "authorChannelId": lambda x: ", ".join(list(set(x))),
    }
    df = (
        df.groupby("textOriginal", as_index=False)
        .agg(agg_dict)
        .sort_values("count", ascending=False)
    )
    df = df.iloc[: min(num, len(df.index)), :]
    df.to_csv("repeat_comments.csv")


if __name__ == "__main__":

    """
    SETUP
    """
    vdb = datasets.VideoDatabase(consts.VIDEOS_CSV)
    vdb.load_from_csv()
    vdb.sync_comments_file(consts.COMMENTS_CSV)

    df = pd.read_csv("comments.csv", usecols=consts.COMMENT_COLS, lineterminator="\n")
    df["channelName"] = df["videoId"].apply(vdb.videoId_to_channelName)

    """
    EXECUTE EXPERIMENTS
    """
    # search_comments(df, "covid")
    # experiment_w2v_comments(df)
    # experiment_clusters()
    experiment_troll_detection(df)
    # experiment_repeats(df, 100)
    # search_histogram(df, "trump")
