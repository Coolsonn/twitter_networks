import os
import tweepy as tw
import pandas as pd
import re
import tqdm

#Give credentials to Twitter developer account:

print('Enter your Twitter API credentials: )
consumer_key= input('consumer key: ')
consumer_secret= input('consumer secret: ')
access_token= input('access token: ')
access_token_secret= input('access token secret: ')
      
#Authenticate and create an API object:
      
auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit=True)
      

#Beginning of scraping:
#First, let's define a function for finding mentions in tweet text:
      
def find_mentions(tweet):
    mentions = re.findall(r'@\w+', tweet)
    return mentions

#Scrape 10 latest tweets of Twitter account (specified by a user). The number of tweets can be extended -- for the purposes of our #research we limited only to 10 due to the limitations of the Free Twitter API access. The code below will:
#1) scrape the tweets, extract username, content and timestamp from these tweets and arrange these data in a dataframe<br>
#2) extract mentions from each of the tweets posted by the accoun owner<br>
#3) create 'nodes' and 'edges' lists, where nodes are people mentioned by a user, and edges are connections between them
      
df_network = pd.DataFrame() 
nodes = []
edges = []

not_iterable = [] 

initial_username = input('Enter screen name of a Twitter user (without @): ')
nodes.append('@' + initial_username)
not_iterable.append('@' + initial_username)

tweets = api.user_timeline(screen_name = f'{initial_username}', count = 10, include_rts = True)

for tweet in tweets:
    data = [tweet.user.screen_name, tweet.text, tweet.created_at]
    df_op = pd.DataFrame(data)
    df_network = df_network.append(df_op.T)

for index in range(df_network.shape[0]):
    mentions_to_list = find_mentions(df_network.iloc[index, 1])
    for mention in mentions_to_list:
        edges.append([('@'+initial_username), mention])
        nodes.append(mention)
      
#The loop below will go through all of the previously mentioned 'nodes' and do exactly the same -- collect profile names that they #mention and append them to 'nodes' and 'edges' list.
#The loop can throw an error due to the limit of tweets downloaded per request
try:
    for user in tqdm.tqdm(nodes):
        if user in not_iterable:
            continue
        else:
            scrap_tweets = api.user_timeline(screen_name = user, count = 10, include_rts = True)

            df_network_op = pd.DataFrame()
            for tweet in scrap_tweets:
                data = [tweet.user.screen_name, tweet.text, tweet.created_at]
                df_op = pd.DataFrame(data)
                df_network = df_network.append(df_op.T)
                df_network_op = df_network_op.append(df_op.T)

            for index in range(df_network_op.shape[0]):
                mentions_to_list = find_mentions(df_network_op.iloc[index, 1])
                for mention in mentions_to_list:
                    edges.append([(user), mention])
                    nodes.append(mention)

            not_iterable.append(user)
except TweepError:
      continue
      
#End of scraping -- time for data processing¶
#Create a list of unique nodes:
      
unique_nodes = []

for node in nodes:
    if node not in unique_nodes:
        unique_nodes.append(node)
      
#Create df_edges dataframe (for edges) and df_unique_nodes dataframe (for unique nodes) and name the columns correctly
      
df_edges = pd.DataFrame(edges)
df_edges.rename(columns={0:'Source',1:'Target'}, inplace=True)
df_edges_copy = df_edges.copy()


df_unique_nodes = pd.DataFrame(unique_nodes)
df_unique_nodes.reset_index(inplace=True)
df_unique_nodes.rename(columns={0:'label', 'index':'id'}, inplace=True)
      
#Join the display names from the df_edges table with account IDs from the df_unique_nodes table.
#According to Gephi rules, edges table should consist of just ID numbers of Source and Target entities.
      
df_edges_processed = df_edges.merge(df_unique_nodes, 
               how='left', 
               left_on='Source', 
               right_on='label').drop(['Source', 'label'], axis=1).rename(columns={'id':'Source'}).merge(df_unique_nodes,
                                                                                                        how='left',
                                                                                                        left_on='Target',
                                                                                                        right_on='label').drop(['Target','label'], axis=1).rename(columns={'id':'Target'})

#Export both files into CSV:
      
df_unique_nodes.to_csv('nodes.csv')
df_edges_processed.to_csv('edges.csv')