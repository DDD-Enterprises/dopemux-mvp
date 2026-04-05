# GraphQL query for fetching PR state
GET_PR_DETAILED_STATE = """
query GetPRDetailedState($owner: String!, $repo: String!, $prNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      id
      number
      title
      author {
        login
      }
      body
      state
      mergeable
      updatedAt
      labels(first: 20) {
        nodes {
          name
        }
      }
      commits(last: 1) {
        nodes {
          commit {
            statusCheckRollup {
              contexts(last: 100) {
                nodes {
                  ... on CheckRun {
                    name
                    status
                    conclusion
                    startedAt
                    completedAt
                  }
                  ... on StatusContext {
                    context
                    state
                  }
                }
              }
            }
          }
        }
      }
      mergeQueueEntry {
        position
        state
        estimatedTimeToMerge
      }
      reviews(first: 50) {
        nodes {
          id
          author { login }
          body
          state
          createdAt
        }
      }
      comments(first: 50) {
        nodes {
          id
          author { login }
          body
          createdAt
        }
      }
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 50) {
            nodes {
              id
              author { login }
              body
              path
              line
              createdAt
            }
          }
        }
      }
    }
  }
}
"""

UPDATE_PULL_REQUEST = """
mutation UpdatePullRequest($pullRequestId: ID!, $title: String, $body: String) {
  updatePullRequest(input: {pullRequestId: $pullRequestId, title: $title, body: $body}) {
    pullRequest {
      id
      title
      body
    }
  }
}
"""

ADD_COMMENT_TO_THREAD = """
mutation AddCommentToThread($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $threadId, body: $body}) {
    comment {
      id
      body
    }
  }
}
"""

RESOLVE_REVIEW_THREAD = """
mutation ResolveReviewThread($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread {
      id
      isResolved
    }
  }
}
"""

ADD_PR_COMMENT = """
mutation AddPRComment($subjectId: ID!, $body: String!) {
  addComment(input: {subjectId: $subjectId, body: $body}) {
    commentEdge {
      node {
        id
        body
      }
    }
  }
}
"""

ENQUEUE_PULL_REQUEST = """
mutation EnqueuePullRequest($pullRequestId: ID!) {
  enqueuePullRequest(input: {pullRequestId: $pullRequestId}) {
    mergeQueueEntry {
      position
      state
    }
  }
}
"""

DEQUEUE_PULL_REQUEST = """
mutation DequeuePullRequest($id: ID!) {
  dequeuePullRequest(input: {id: $id}) {
    clientMutationId
  }
}
"""
