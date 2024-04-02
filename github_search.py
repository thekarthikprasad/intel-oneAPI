# -*- coding: utf-8 -*-
"""Github-Search.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1t5PA8Q-ZnE1Z3KUt7zs9YNA9SlnnW0_j
"""

from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
import time

import requests
from bs4 import BeautifulSoup
import json

def fetch_file_tree(repo_owner, repo_name, branch='main'):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/git/trees/{branch}?recursive=1'
    response = requests.get(url)
    data = response.json()

    file_tree = []
    for item in data.get('tree', []):
        if item['type'] == 'blob':
            file_tree.append(item['path'])
        elif item['type'] == 'tree':
            subtree = fetch_file_tree(repo_owner, repo_name, branch=item['path'])
            file_tree.extend([f"{item['path']}/{subfile}" for subfile in subtree])
    return file_tree

def parse_code_from_github(url):
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find("script", {"type": "application/json", "data-target": "react-app.embeddedData"})
    json_data = script_tag.string
    parsed_data = json.loads(json_data)
    code_lines = parsed_data['payload']['blob']['rawLines']
    return '\n'.join(code_lines)

def parse_ipynb_from_github(url):
    query = url.replace("https://github.com/", "").replace("/blob/", "/").replace("github", "nbviewer") + "?flush_cache=true"
    response = requests.get(f"https://nbviewer.jupyter.org/{query}")
    return response.text

def fetch_and_parse_files(repo_owner, repo_name, file_paths):
    for path in file_paths:
        if path.endswith('.ipynb'):
            code = parse_ipynb_from_github(f"https://github.com/{repo_owner}/{repo_name}/blob/main/{path}")
        else:
            code = parse_code_from_github(f"https://github.com/{repo_owner}/{repo_name}/blob/main/{path}")
        print(f"Code from {path}:")
        print(code)
        print("-----------------------")

def main():
    repository_owner = 'krishnaik06'
    repository_name = 'Student-Performance-Azure-deployment'
    branch_name = 'main'

    print(f"Fetching file tree for '{repository_owner}/{repository_name}' (branch: {branch_name}):")
    file_tree = fetch_file_tree(repository_owner, repository_name, branch=branch_name)
    print(file_tree)
    print("\nParsing specific files:")
    fetch_and_parse_files(repository_owner, repository_name, file_tree)

if __name__ == "__main__":
    main()

query = """"
You are an intelligent search query modeler. you model search queries based on the user prompt.
Your task is to model a search query based on the user input.
The user inputs a complete description of his problem, you have to find the underlying context, and find key entities
Based on the problem, you have to model a search query to search in github.
Github uses keyword based search results, so you have to provide search query in such a way that, we end up in appropriate search results.
I provide you some tips to model a search query, and also some github search specifics so you can follow that

Instructions:

-A thing to note when you search by Name and description of the README file is that your search phrase should begin with the in qualifier. This makes it possible to search "inside" what you are looking for.

Example

Using in:name. Let's say you are looking for resources to learn more about Data Science. In this case, you can use the command Data Science in:name which will list repositories with Data Science in the repository name.

Using in:description. If you want to find repositories with a ceratin description, for example repositories where the term "freeCodeCamp" is included in the descriptionm, our search will be: freecodecamp in:description

Using in:readme. You use this to search through a README of a file for a certain phrase. If we want to find repositories where the term freecodecamp is included in the README, our search will be: freecodecamp in:readme.

Using in:topic. You use this to find if a certain phrase or word is labeled in the topics. For example to find all repositories where freecodecamp is listed in the topic, our search will be: freecodecamp in:topic

You can also combine multiple search queries to further narrow down the search.

-How to Find by Stars, Forks
You can also search for a repository based on how many stars and forks the project has. This makes it easier for you to know how popular the project is.

Examples

Using stars:n. If you search for a repository with 1000 stars, then your search query will be stars:1000. This will list repositories with exactly 1000 stars.

Using forks:n. This specifies the number of forks a repository should have. If you want find repositories that have less than 100 forks, your search will be: forks:<100.

The good thing is that you can always use relational operators like <, >, <=, >= & .. to help you further narrow your search.

-How to Find by Language
Another cool way to search through GitHub is by language. This helps you filter out repositories to a specific language.

Example:

-Using language:LANGUAGE. For example if you want to find repositories written in PHP, your search will be: language:PHP
How to Find by Organization Name
You can also search repositories/projects that are maintained or created by a specific organization. For this you need to begin your search with the keyword org:... followed by the organization name.

For example if you search org:freecodecamp it will list repositories that match freeCodeCamp.

-How to Find by Date
If you want your results based on a specific date, you can search using one of these keywords: created, updated, merged and closed. These keywords should be accompanied by date in the format YYYY-MM-DD.

Example:

Using keyword:YYYY-MM-DD. Take an instance where we want to make a search of all repositories with the word freeCodeCamp that were created after 2022-10-01. Then our search will be: freecodecamp created:>2022-10-01
You can also use <, >, >= and <= to search for dates after, before and on the specified date. To search within a range you can use ....

-How to Find by License
Licenses are very important when you are are looking for a project to contribute to. Different licenses give different rights as to what a contributor can do or can not do.

To make it easier for you to find projects with right licenses you need to have a good understanding of licenses. You can read more about them here.

Example:

Using license:LICENSE_KEYWORD. This is a good way to search for projects with specific licenses. To search projects with the MIT license, for instance, you would do license:MIT.
How to Find by Visibility

-You can also conduct your search in terms of the visibility of the repository. In this case you can either use public or private. This will match issues and PRs that are either in a public or private repository, respectively.

Examples:

Using is:public. This will show a list of public repositories. Let's take an isntance where we want to search all public repositories owned by freeCodCamp. Then our search will be: is:public org:freecodecamp.
Using is:private. This query is meant to lists all private repositories under the given search query.



Here are even more extra tips:

*you can utilize common filter, sort, and searching techniques to easily find specific issues and pull requests of a given project.
*is:issue is:open label:beginner - This particular query will list all projects with issues that are open and labeled beginner.
*is:issue is:open label:easy - This will list all open issues that are labeled easy.
*is:issue is:open label:first-timers-only - This lists all open issues that welcome first-timer contributions.
*is:issue is:open label:good-first-bug - This lists projects with open issues labeled good-first-bug, to attract contributors to work on them.
*is:issue is:open label:"good first issue" - This will list all open issues with the label good first issue, meaning it is good for place for beginners to get started.
*is:issue is:open label:starter - This lists all open issues from across GitHub that are labeled starter.
*is:issue is:open label:up-for-grabs - This lists open issues that are ready to be worked on if you have the necessary skills.
*no:project type:issue is:open - This will list all open issues that are not assigned to a specific project.
*no:milestone type:issue is:open - Many times, projects are tracked with milestones. But if you want to find issues that are not tracked, this search query will list those projects for you.
*no:label type:issue is:open - This lists all open issues that are not labeled.
*is:issue is:open no:assignee - This shows all open issues that have not yet been assigned to a person.

Its not necessary that you use all the tips, you can use when required.

Criteria: You have to model search queries in a way that ends up in more accurate results in github. always consider the user's requirement while generating
You can model accurate search query, even more than one if required.. but make sure it ends up with rich results.

Constraints: Your search query should exactly narrow down to user's problem..
Input: Here is the user query: {user_prompt}

Output: Search query must solve the user problem, use a filter/combination of filters whenever necessary.
generate accurate search queries solving user's purpose.
Dont give generic quries.
Dont give results as filters alone, your output should compulsarily have a search term close to user query.
give answer as json
{chat_history}
"""

llm = ChatGroq(temperature=0, groq_api_key="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", model_name="mixtral-8x7b-32768")

prompt = PromptTemplate.from_template(template=query)

memory = ConversationBufferMemory(memory_key="chat_history")

chain = LLMChain(
            llm=llm,
            prompt=prompt,
            verbose=True,
            memory=memory)

response = chain.predict(user_prompt=user_prompt)

parser = JsonOutputParser()

prompt = PromptTemplate(
    template=query1,
    input_variables=["user_prompt"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = prompt | llm | parser

chain.invoke({"user_prompt":user_prompt, "chat_history":memory })

query = """
Now based on the user prompt, we narrowed down search results from the github api... your task is to analyse the file tree, and tell which files of the repo are required to be analysed
Important points:
- while picking files to be analysed, check with user prompt understanding and analyse...
- Pick required files
- you can pick documentation files, readme and other things - to make a contextual understanding of the repo..
- give file along with folder paths
- result set must contain only required files to be analysed, not anything else
- Model result as json
here is the file tree: {file_tree}
you:
{chat_history}

"""

prompt = PromptTemplate.from_template(template=query)

chain = LLMChain(
            llm=llm,
            prompt=prompt,
            verbose=True,
            memory=memory)

repo_tree = get_file_tree('https://api.github.com/repos/Adam-Abera/Personal_Learning_Assistant/git/trees/main?recursive=1')

chain.predict(file_tree=repo_tree)

import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

docs = SimpleDirectoryReader("/content/Data").load_data()

system_prompt = """
You are a code analyzer. you have to analyse the code semantically and understand the meaning of it.
user will provide his context, based on that you recommend the appropriate code repository
"""

query_wrapper_prompt = SimpleInputPrompt("<|USER|>{query_str}<|ASSISTANT|>")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)

embeddings = OllamaEmbeddings(model="mistral")

def format_docs(docs):
  return "\n\n".join(doc.page_content for doc in docs)