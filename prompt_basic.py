import json
import random
import re

import jieba
import jieba.posseg as pseg

import numpy as np

from scrape_twitter import process_tweet_ids
import config

original_post_prompt = [
"最近过得怎么样？",
"你这段时间都在忙什么？",
"离我们上次见面以来，有什么新鲜事吗？",
"最近有什么有趣的经历吗？",
"你近期的生活如何？",
"距离我们上次见面已经过了一段时间了，你过得好吗？",
"你最近都在做些什么？",
"近期有什么重要的变化吗？",
"有什么新的发展吗？",
"能和我分享一下你近期的生活吗？",
"你最近有什么特别的事情发生吗？",
"你最近的生活有什么变化吗？",
"最近有没有什么大事发生？",
"过去的几个月里，你都经历了些什么？",
"你过去一段时间都在忙些什么？",
"有什么新鲜事要和我分享吗？",
"这段时间有没有什么让你难忘的事情发生？",
"最近在工作或生活方面有什么挑战吗？",
"从我们上次见面到现在，你都遇到了哪些有意思的事情？",
"过去几个月你都忙些什么？",
"最近你都有哪些新发现？",
"你近期有哪些值得分享的经历？",
"跟我聊聊你最近的日常吧？",
"近期有什么值得一提的事吗？",
"这段时间有没有什么特别的回忆？",
"最近有没有什么让你感到骄傲的事？",
"你最近有什么惊喜发生吗？",
"过去一段时间，你的生活中有哪些亮点？",
"近来你都有哪些新的尝试？",
"你最近的日子过得怎样？有什么精彩的时刻？",
"这段时间有什么特别的见闻吗？",
"从上次见面到现在，你有什么有趣的故事吗？",
"最近有没有什么特殊的事情让你感到开心？",
"你最近有什么新的梦想或目标吗？",
"过去的一段时间里，你有什么难忘的经历吗？",
"你最近有没有什么特别的发现或灵感？",
"最近有没有什么突破性的成就？",
"这段时间你都学到了哪些新知识？",
"最近有没有什么值得一提的事情发生在你身边？",
"最近你有什么值得庆祝的事情吗？",
"从我们上次见面以来，你都有哪些新的探险？",
"最近有没有什么让你感到充实的事情？",
"过去一段时间里，你有什么特别的体验？",
"你近期有什么令人惊讶的收获？",
"跟我分享一下你最近的喜怒哀乐吧？"
]

related_topic_prompt = [
    "关于[AAA]，你有什么想法？",
    "你觉得[AAA]在日常生活中扮演着什么角色？",
    "你曾经与[AAA]有过什么相关经历吗？",
    "你觉得[AAA]有哪些相关的话题值得探讨？",
    "关于[AAA]，你有什么好的经验可以分享吗？",
    "你如何看待[AAA]与我们生活中的其他方面的关系？",
    "你觉得[AAA]有哪些值得关注的趋势？",
    "你认为[AAA]对于我们的日常生活有多大意义？",
    "你觉得[AAA]有哪些令人好奇的方面？",
    "你有没有关于[AAA]的有趣故事？",
    "你觉得[AAA]有哪些令人欣赏的方面？",
    "关于[AAA]，你觉得有哪些有趣的讨论点？",
    "关于[AAA]，你有什么新的见解吗？",
    "你觉得[AAA]是如何影响你生活的？",
    "你曾经有过关于[AAA]的有趣经历吗？",
    "关于[AAA]，有哪些热门话题值得关注？",
    "你有没有关于[AAA]的特别记忆？",
    "你觉得[AAA]与你生活中的其他元素有何联系？",
    "你觉得[AAA]有哪些令人惊讶的方面？",
    "你有没有听过关于[AAA]的趣闻轶事？",
    "关于[AAA]，你觉得有哪些引人入胜的话题？",
    "你对[AAA]有哪些深刻的印象？",
    "你有没有关于[AAA]的奇闻异事？",
    "关于[AAA]，你有什么特别的见解吗？",
    "你有没有关于[AAA]的特别喜好？",
    "你对[AAA]有哪些独到的见解？",
    "你觉得[AAA]如何影响我们的思考方式？",
    "你有没有关于[AAA]的趣味事例？",
    "你觉得[AAA]有哪些令人叹为观止的特点？",
    "关于[AAA]，你有什么富有启发性的想法？",
    "你有没有关于[AAA]的奇特经历？",
    "你觉得[AAA]有哪些吸引人的特质？",
    "关于[AAA]，你有什么令人兴奋的见解？"
]

def cut_sent(text):
    sub_sentences = re.split(r'([\。|\！|\？|\；|\，|\n])', text)
    sub_sentences = [s1 + s2 for s1, s2 in zip(sub_sentences[0::2], sub_sentences[1::2])] + ([sub_sentences[-1]] if len(sub_sentences) % 2 == 1 else [])
    return [s.replace("\n", "") for s in sub_sentences if (s.strip() != "" and s.strip() != "(media)" and s.strip() != "(link)")]


def findTopic(md):
    substring = cut_sent(md)
    if len(substring) > 1:
        rr = random.randint(0, len(substring)-1)
        # choose a random substring, maximum length is 5
        topic = substring[rr]
        # cut off the last word, if it's a chinese punctuation
        if topic[-1] in ["，", "。", "！", "？", "；"]:
            topic = topic[:-1]

        # use jieba to do the word segmentation and pos tagging
        tokens = [word for word,flag in pseg.cut(topic) if 'n' in flag] 
        if len(tokens) > 0:
            topic = random.choice(tokens)
        else:
            # it's just it.
            topic = topic

        instruction = random.choice(related_topic_prompt).replace("[AAA]", topic)
        return instruction
    else:
        return None


def checkResponse(response):
    # check if the user's response is too short. Filter it out. 
    if len(response.replace("\n","").replace(" ", "").replace("(media)","").replace("(link)", "")) < config.RESPONSE_THRESH:
        return False
    return True

def write_json(md_path, final_md, lang):
    

    # construct a instruction dataset    
    final = []

    # construct a list of tweets to be downloaded to sample the contexts
    context_tweets = []

    for loop in range(config.AUGMENTATION_FACTOR_ORIGINAL):
        for id, md, in_reply_to, quote, retweet in final_md:

            # content filter goes here:
            if md.strip() == "(media)":
                continue

            reply_indication = "reply to other user"
            quote_indication = "quote of other's tweet"
            retweet_indication = "retweet of other's tweet"

            if in_reply_to and quote:
                # todo: process replies and quotes
                pass
            elif in_reply_to:
                # save them into a list; we will download them later
                context_tweets.append({"id": id, "text": md})
            elif quote:
                # todo: process quotes
                pass
            elif retweet:
                # not my tweet, simply discard them
                pass
            else:
                # in this version we only care about the original post, 
                # for faster convergence of the model and simple observation of the overall system

                # sample a random float from 0-1 to decide the ways of generation
                # sample_range is a probablity accumulative list
                # [random post, completion, Q&A, rest (direct original post)]
                if config.PARSE_REPLIES:
                    # if we parse the replies, we will have more data to sample from
                    # we do not need to do the completion, and the Q&A part can be inferred from the in-reply-to
                    # of the original posts, 40% are unconditional (with questions), 10% are completion, 20% are Q&A, 30% are unconditional (with no prompts)
                    sample_range = [0.4, 0.5, 0.7, 1]
                else:
                    sample_range = [0.35, 0.5, 0.95, 1]
                rr = random.random()
                if rr < sample_range[0]:
                    # sample a random question, and concatenate
                    instruction = f"{random.choice(original_post_prompt)}"
                    user_input = f""
                    if checkResponse(md):
                        final.append({"instruction": instruction, "input": user_input, "output": md})
                elif rr < sample_range[1]:
                    # given a truncated tweet, ask for completion
                    substring = cut_sent(md)
                    if len(substring) > 1:
                        user_input = f""
                        rr = random.randint(1, len(substring)-1)
                        instruction = "".join(substring[0:rr])
                        if checkResponse(instruction):
                            final.append({"instruction": instruction, "input": user_input, "output": "".join(substring[rr:])})
                    else:
                        instruction = f"{random.choice(original_post_prompt)}"
                        user_input = f""
                        final.append({"instruction": instruction, "input": user_input, "output": md})
                elif rr < sample_range[2]:
                    # QA like 
                    # ask for a topic, the topic is mainly based on a substring of this tweet
                    instruction = findTopic(md)
                    if instruction is not None:
                        user_input = f""
                        if checkResponse(md):
                            final.append({"instruction": instruction, "input": user_input, "output": md})
                    else:
                        #if cannot find a topic
                        instruction = f"{random.choice(original_post_prompt)}"
                        user_input = f""
                        if checkResponse(md):
                            final.append({"instruction": instruction, "input": user_input, "output": md})

                else:
                    # no instructions, unconditional generation.
                    final.append({"instruction": "", "input": "", "output": md})

    if config.PARSE_REPLIES:
        # Now things get even more interesting, we will scrape the tweets from the context_tweet_ids
        parsed_tweets = process_tweet_ids(context_tweets)
        print(f"Processed {len(parsed_tweets)} tweets from the context tweets.")

        for l in range(config.AUGMENTATION_FACTOR_REPLIES):
            for index, t in enumerate(parsed_tweets):
                #print(index, t)
                tweet_id = t['id']
                tweet_text = t['text']
                context = t['context']

                # first, we need to check if the reply itself is interesting
                if not checkResponse(tweet_text):
                    continue

                # then, we need to check if the context is blank
                if context is None:
                    continue

                if len(context) == 0:
                    continue
                
                # next, we do a rough check in if the context is interesting
                # if the context is too short, we will not use it
                if not checkResponse("".join(context)):
                    continue

                # We believe the context is interesting
                # in this way, we want to sample a random context length based on the probability distribution of 1/x
                # the longer the context, the less likely it will be sampled
                # if the context's length is not long enough, we will sample again
                l = len(context)
                p = []
                for j in range(l):
                    p.append(1/float(j+1))

                # normalize the probability
                p = np.array([i/sum(p) for i in p], dtype=np.float32)

                while True:
                    # sample a number based on p
                    r = np.random.choice(l, 1, p=p)[0]

                    # then we will sample the last r tweets from the context
                    # and concatenate them together
                    # TODO: prompt engineering from different threads, now it's simply as a \n
                    context_text = "\n".join(context[-r:])
                    # check if the context is interesting
                    if checkResponse(context_text):
                        break

                # now we have a context, and a reply
                # go give the prompt
                final.append({"instruction": context_text, "input": "", "output": tweet_text})

                # but we can do more, we can also augment a Q&A like discussion within the topic, if we want
                # give a small random chance to do this
                if random.random() < 0.1:
                    instruction = findTopic(context[-1])
                    if instruction is not None:
                        final.append({"instruction": instruction, "input": "", "output": tweet_text})

                # TODO: any other sort of prompt engineering?

    with open(md_path, "w") as f:
        # shuffle the dataset
        random.shuffle(final)
        f.write(json.dumps(final, indent=4, ensure_ascii=False))
