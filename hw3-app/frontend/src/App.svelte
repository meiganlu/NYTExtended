<script lang="ts">
  import { onMount } from 'svelte';
  import Comment from './Comment.svelte';

  let today = '';
  let imageArticles: any[] = [];
  let loadError = '';

  let showAcct = false;
  let email: string | null = '';
  const loggedIn = () => !!email;                         

  type CommentT = {
    id: string; content: string; user_name: string;
    created_at: string; children?: CommentT[];
  };

  const comments: Record<string, CommentT[]> = {};
  const drawerOpen: Record<string, boolean> = {};
  const newTop:   Record<string, string>    = {};
  const replyOpen:Record<string, boolean>   = {};
  const replyBox: Record<string, string>    = {};

  let commentCounts: Record<string, number> = {};

  function getImage(a: any): string | null {
    if (a?.multimedia?.default?.url)   return a.multimedia.default.url;
    if (a?.multimedia?.thumbnail?.url) return a.multimedia.thumbnail.url;
    return null;
  }

  function redirectToDex() {
    window.location.href = 'http://localhost:8000/login';
  }

  onMount(async () => {
    today = new Date().toLocaleDateString('en-US',
      { weekday:'long', month:'long', day:'numeric', year:'numeric' });

    const url = new URL(window.location.href);
    email = url.searchParams.get('user');

    try {
      const r = await fetch('/api/local-news', { credentials:'include' });
      const j = await r.json();
      imageArticles = (j.response?.docs || []).filter(getImage);
      
      if (imageArticles.length > 0 && loggedIn()) {
        await Promise.all(imageArticles.map(async (article) => {
          if (article._id) {
            await fetchCommentCount(article._id);
          }
        }));
      }
      
      const lastOpenDrawer = localStorage.getItem('openArticleDrawer');
      if (lastOpenDrawer && loggedIn()) {
        drawerOpen[lastOpenDrawer] = true;
        await fetchComments(lastOpenDrawer);
      }
    } catch (e) {
      loadError = 'Could not load news.';
      console.error(e);
    }
  });

  async function fetchCommentCount(aid: string) {
    try {
      const safe = encodeURIComponent(aid);
      const r = await fetch(`/api/comments/${safe}`, { credentials:'include' });
      
      if (r.ok) {
        const commentsData = await r.json();
        const countNestedComments = (comments: any[]): number => {
          let count = comments.length;
          for (const comment of comments) {
            if (comment.children && comment.children.length) {
              count += countNestedComments(comment.children);
            }
          }
          return count;
        };
        
        commentCounts[aid] = countNestedComments(commentsData);
      }
    } catch (error) {
      console.error(`Failed to fetch comment count for ${aid}:`, error);
      commentCounts[aid] = 0;
    }
  }
  
  async function fetchComments(aid: string) {
    try {
      const safe = encodeURIComponent(aid);
      const r = await fetch(`/api/comments/${safe}`, { credentials:'include' });
      
      if (r.ok) {
        const commentsData = await r.json();
        comments[aid] = commentsData;
        
        const countNestedComments = (comments: any[]): number => {
          let count = comments.length;
          for (const comment of comments) {
            if (comment.children && comment.children.length) {
              count += countNestedComments(comment.children);
            }
          }
          return count;
        };
        
        commentCounts[aid] = countNestedComments(commentsData);
      } else {
        console.error(`Error fetching comments: ${r.status}`);
        comments[aid] = []; 
        commentCounts[aid] = 0;
      }
    } catch (error) {
      console.error('Failed to fetch comments:', error);
      comments[aid] = []; 
      commentCounts[aid] = 0;
    }
  }
  
  async function post(aid: string, parentId: string | null, text: string) {
    if (!loggedIn() || !text.trim()) return;
    try {
      const safe = encodeURIComponent(aid);
      const r = await fetch(`/api/comments/${safe}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 
          content: text.trim(), 
          parent_id: parentId 
        }),
        credentials: 'include'
      });
      
      if (r.ok) {
        if (parentId) {
          replyBox[parentId] = '';
          replyOpen[parentId] = false;
        } else {
          newTop[aid] = '';
        }
        
        await fetchComments(aid);
      } else {
        console.error(`Error posting comment: ${r.status}`);
        alert('Failed to post comment. Please try again.');
      }
    } catch (error) {
      console.error('Failed to post comment:', error);
      alert('Failed to post comment. Please try again.');
    }
  }
  
  async function handleDelete(cid: string, aid: string) {
    if (!confirm('Delete this comment?')) return;
    try {
      const r = await fetch(`/api/comments/${cid}`, { 
        method: 'DELETE', 
        credentials: 'include' 
      });
      
      if (r.ok) {
        await fetchComments(aid);
      } else {
        console.error(`Error deleting comment: ${r.status}`);
        alert('Failed to delete comment. Please try again.');
      }
    } catch (error) {
      console.error('Failed to delete comment:', error);
      alert('Failed to delete comment. Please try again.');
    }
  }

  async function handleRedact(cid: string, aid: string) {
    const selection = window.getSelection();
    const selectedText = selection ? selection.toString() : '';

    if (!selectedText) return;
    if (!confirm(`Redact selected text: "${selectedText}"?`)) return;

    try {
      const res = await fetch(`/api/comments/${cid}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ textToRedact: selectedText, authorId: aid }),
      });

      if (!res.ok) {
        throw new Error(`Server responded with status ${res.status}`);
      }

      window.location.reload();
    } catch (error) {
      console.error("Failed to redact comment:", error);
      alert("Failed to redact comment. Please try again.");
    }
  } 

  
  function handleReply(aid: string, cid: string, send = false) {
    if (send) {
      post(aid, cid, replyBox[cid]);
    } else {
      replyOpen[cid] = !replyOpen[cid];
      if (!replyBox[cid]) {
        replyBox[cid] = '';
      }
    }
  }


  function openDrawer(aid: string) {
    if (!loggedIn()) return;         

    Object.keys(drawerOpen).forEach(key => {
      if (drawerOpen[key] && key !== aid) {
        drawerOpen[key] = false;
      }
    });
    
    drawerOpen[aid] = true;
    
    localStorage.setItem('openArticleDrawer', aid);
    
    if (!comments[aid]) {
      fetchComments(aid);
    }
  }
  
  function closeDrawer(aid: string) {
    drawerOpen[aid] = false;
    
    localStorage.removeItem('openArticleDrawer');
  }
</script>

<main>
  <header class="site-header">
    <div class="date">
      <p><b>{today}</b><br/>Today's Paper</p>
    </div>

    <img class="logo" src="/NYTimeslogo.png" alt="The New York Times" />

    <div class="top-right">
      {#if !loggedIn()}
        <button class="button" on:click={redirectToDex}>Log in</button>
      {:else}
        <button class="acct-btn" on:click={() => showAcct = true}>Account</button>
      {/if}
    </div>
  </header>

  {#if showAcct}
    <div class="overlay" on:click={() => showAcct = false}></div>
    <aside class="acct-drawer">
      <button class="close" on:click={() => showAcct = false}>×</button>
      <p class="acct-email"><b>{email}</b></p>
      <hr>
      <h2 class="greeting">Good&nbsp;afternoon.</h2>
      <button class="logout" on:click={() => window.location.href='/logout'}>Log&nbsp;out</button>
    </aside>
  {/if}

  {#if loadError}
    <p class="err">{loadError}</p>
  {:else if !imageArticles.length}
    <p class="loading">Loading articles…</p>
  {:else}
    <div class="main-container">
      <div class="left-column">
        {#each [2,3] as idx}
          {#if imageArticles[idx]}
            {@const art=imageArticles[idx]}
            <article class="card">
              <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
              <h2>{art.headline.main}</h2>
              <p>{art.abstract}</p>
              <button class="count-btn" on:click={() => openDrawer(art._id)}>
                💬 {commentCounts[art._id] || 0}
              </button>
            </article>
          {/if}
        {/each}
      </div>

      <div class="mid-column">
        {#if imageArticles[0]}
          {@const art=imageArticles[0]}
          <article class="card lead">
            <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
            <h1>{art.headline.main}</h1>
            <p>{art.abstract}</p>
            <button class="count-btn" on:click={() => openDrawer(art._id)}>
              💬 {commentCounts[art._id] || 0}
            </button>
          </article>
        {/if}

        {#if imageArticles[1]}
          {@const art=imageArticles[1]}
          <article class="card medium">
            <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
            <h3>{art.headline.main}</h3>
            <p>{art.abstract}</p>
            <button class="count-btn" on:click={() => openDrawer(art._id)}>
              💬 {commentCounts[art._id] || 0}
            </button>
          </article>
        {/if}
      </div>

      <div class="right-column">
        {#each [5,7] as idx}
          {#if imageArticles[idx]}
            {@const art=imageArticles[idx]}
            <article class="card">
              <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
              <h2>{art.headline.main}</h2>
              <p>{art.abstract}</p>
              <button class="count-btn" on:click={() => openDrawer(art._id)}>
                💬 {commentCounts[art._id] || 0}
              </button>
            </article>
          {/if}
        {/each}
      </div>

      <div class="side-columns">
        {#each [2,3] as idx}
          {#if imageArticles[idx]}
            {@const art=imageArticles[idx]}
            <article class="card">
              <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
              <h2>{art.headline.main}</h2>
              <p>{art.abstract}</p>
              <button class="count-btn" on:click={() => openDrawer(art._id)}>
                💬 {commentCounts[art._id] || 0}
              </button>
            </article>
          {/if}
        {/each}
        {#each [5,7] as idx}
          {#if imageArticles[idx]}
            {@const art=imageArticles[idx]}
            <article class="card">
              <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
              <h2>{art.headline.main}</h2>
              <p>{art.abstract}</p>
              <button class="count-btn" on:click={() => openDrawer(art._id)}>
                💬 {commentCounts[art._id] || 0}
              </button>
            </article>
          {/if}
        {/each}
      </div>
    </div>
  {/if}

  {#each Object.keys(drawerOpen) as aid (aid)}
    {#if drawerOpen[aid]}
      <div class="overlay" on:click={() => closeDrawer(aid)}></div>
      <aside class="drawer">
        <button class="close" on:click={() => closeDrawer(aid)}>×</button>
        <h2><strong>{imageArticles.find(a=>a._id===aid)?.headline?.main}</strong></h2>
        <hr>
        
        <div class="new-box">
          <h1> Comments {commentCounts[aid] || 0} </h1>
          <textarea
            rows="2"
            bind:value={newTop[aid]}
            placeholder="Share your thoughts."
            disabled={!loggedIn()}>
          </textarea>
          <button
            class="post"
            disabled={!loggedIn() || !newTop[aid]?.trim()}
            on:click={() => post(aid,null,newTop[aid])}>
            Post
          </button>
        </div>

        {#if comments[aid]?.length}
          {#each comments[aid] as c (c.id)}
            <Comment
              {c}
              articleId={aid}
              depth={0}
              doDelete={(id)=>handleDelete(id,aid)}
              doReply={(id,send)=>handleReply(aid,id,send)}
              doRedact={(id)=>handleRedact(id,aid)}
              {replyOpen} {replyBox} />
          {/each}
        {:else}
          <p class="none">No comments yet</p>
        {/if}
      </aside>
    {/if}
  {/each}
</main>