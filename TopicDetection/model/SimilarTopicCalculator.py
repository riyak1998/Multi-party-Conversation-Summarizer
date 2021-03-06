import gensim
import sys
import math
# from Model import Model

import numpy as np
class Model:
    def __init__(self, messages, tokenizer):
        self.tokenizer = tokenizer
        self.innerModel = self.trainNewModel(messages)
        self.index2wordSet = set(self.innerModel.wv.index2word)

    def trainNewModel(self, messages):
        return gensim.models.Word2Vec(
            [self.tokenizer.stemAndTokenize(message) for message in messages],
            min_count = 1)

    def __getitem__(self, index):
        return self.innerModel[index]

    def calculateSimilarity(self, messageA, messageB, indexDistance):
        fullTokensA = self.tokenizer.stemAndTokenize(messageA)
        fullTokensB = self.tokenizer.stemAndTokenize(messageB)

        width = 10
        startA = 0
        best = (float('inf'), 0) # orthogonal
        decay = (0.993 ** indexDistance) # must be related to the cosine threshold
        while startA < len(fullTokensA):
            startB = 0
            tokensA = fullTokensA[int(startA):int(startA + width)]
            while startB < len(fullTokensB):
                # print(" 1 :",startB," 2 : ",width)
                tokensB = fullTokensB[int(startB):int((startB + width))]
                cosine = self.innerModel.n_similarity(tokensA, tokensB) * decay
                centroid = self.centroidDistance(tokensA, tokensB) / decay
                pair = (centroid, cosine)
                if best is None or best > pair:
                    best = pair
                startB = startB + width / 2
            startA = startA + width / 2
        return best

    def centroidDistance(self, tokensA, tokensB):
        centroidA = sum([self[t] for t in tokensA]) / len(tokensA)
        centroidB = sum([self[t] for t in tokensB]) / len(tokensB)
        return np.linalg.norm(self.centroid(tokensA) - self.centroid(tokensB))

    def centroid(self, tokens):
        return sum([self[t] for t in tokens]) / len(tokens)


class SimilarTopicCalculator:
    def __init__(self, window, messages, tokenizer):
        self.window = window
        self.model = Model(messages, tokenizer)

    def calculate(self, message):
        similarities = []
        for topic in self.window.getTopics():
            for topic_message in topic.getMessages():
                (centroidDistance, cosine) = self.model.calculateSimilarity(
                    message, topic_message, message.getID() - topic_message.getID())
                similarities.append(TopicSimilarity(topic, cosine, centroidDistance))
        similarities.sort(key=lambda x: x.getCentroidDistance())
        # get top 5 percent
        size = int(math.ceil(len(similarities) * 5. / 100))
        similarities = similarities[0:size]
        similarities.sort(key= lambda x: -x.getScore())
        return None if len(similarities) == 0 else similarities[0]

class TopicSimilarity:
    def __init__(self, topic, score, centroidDistance):
        self.topic = topic
        self.score = score
        self.centroidDistance = centroidDistance

    def getTopic(self):
        return self.topic

    def getScore(self):
        return self.score

    def getCentroidDistance(self):
        return self.centroidDistance
