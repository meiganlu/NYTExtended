<script lang="ts">
  import { onMount } from 'svelte';

  let apiKey: string = '';
  let today = '';
  let articles: any[] = [];
  let imageArticles: any[] = [];
  let showTab: boolean = false;
  let isAuthenticated: boolean = true;
  let accessToken: string | null = null;
  let email: string | null = '';

  function getImage(article: any): string | null {
    if (article?.multimedia?.default?.url) {
      return article.multimedia.default.url;
    } else if (article?.multimedia?.thumbnail?.url) {
      return article.multimedia.thumbnail.url;
    }
    return null;
  }

  function redirectToDex() {
    // const dexURL = "http://127.0.0.1:5556/auth?client_id=example-app&redirect_uri=http://localhost:3000/callback&response_type=code&scope=openid%20email";
    const dexURL = "http://localhost:8000/login"
    window.location.href = dexURL;
  }

  function toggleSideTab() {
    showTab = !showTab;
  }

  onMount(async () => {
    const now = new Date();
    today = now.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });

    const url = new URL(window.location.href);
    email = url.searchParams.get('user');

    try {
      const res = await fetch('http://localhost:8000/api/local-news');
      const data = await res.json();
      articles = data.response?.docs || [];
      imageArticles = articles.filter(article => getImage(article));
    } catch (error) {
      console.error('Failed to fetch API key:', error);
    }
  }); 
</script>

<main>
  <header>
    <div class="top-right">
      {#if !isAuthenticated}
        <button class="button" on:click={redirectToDex}>LOG IN</button>
      {:else}
        <button class="account" on:click={toggleSideTab}>
          <img src="/account.svg" alt="account tab"/>
        </button>

      {/if}
    </div>
    <div class="date">
      <p><b>{today}</b><br/> Today’s Paper</p>
      <br />
    </div>
    <br>
    <div class="logo-image">
      <img src="/NYTimeslogo.png" alt="The New York Times"/>
    </div>
    <hr style="margin: 1% 2% 2% 2%; width: 95%" />
  </header>

  {#if showTab}
    <aside class="sidebar">
      <p><strong>{email}</strong></p>
      <h1>Good Afternoon.</h1>
    </aside>
  {/if}

  {#if imageArticles.length > 0}
    <div class="main-container">
      <div class="left-column">
        <img src={getImage(imageArticles[2])} alt={imageArticles[2].headline.main}/>
        <h2>{imageArticles[2].headline.main}</h2>
        <p>{imageArticles[2].abstract}</p>
        <p>{imageArticles[2].lead_paragraph}</p>
        <hr style="margin: 2% 0% 10% 0%"/>

        <img src={getImage(imageArticles[3])} alt={imageArticles[3].headline.main}/>
        <h2>{imageArticles[3].headline.main}</h2>
        <p>{imageArticles[3].abstract}</p>
        <p>{imageArticles[3].lead_paragraph}</p>
      </div>

      <div class="mid-column">
        <img src={getImage(imageArticles[0])} alt={imageArticles[0].headline.main}/>
        <h1>{imageArticles[0].headline.main}</h1>
        <p>{imageArticles[0].abstract}</p>
        <p>{imageArticles[0].lead_paragraph}</p>
        <hr style="margin: 1% 0% 5% 0%"/>

        <img src={getImage(imageArticles[1])} alt={imageArticles[1].headline.main}/>
        <h3>{imageArticles[1].headline.main}</h3>
        <p>{imageArticles[1].abstract}</p>
        <p>{imageArticles[1].lead_paragraph}</p>
      </div>

      <div class="right-column">
        <img src={getImage(imageArticles[5])} alt={imageArticles[5].headline.main}/>
        <h2>{imageArticles[5].headline.main}</h2>
        <p>{imageArticles[5].abstract}</p>
        <p>{imageArticles[5].lead_paragraph}</p>
        <hr style="margin: 2% 0% 10% 0%"/>

        <img src={getImage(imageArticles[7])} alt={imageArticles[7].headline.main}/>
        <h2>{imageArticles[7].headline.main}</h2>
        <p>{imageArticles[7].abstract}</p>
        <p>{imageArticles[7].lead_paragraph}</p>
      
      </div>

      <div class="side-columns">
        <img src={getImage(imageArticles[2])} alt={imageArticles[2].headline.main}/>
        <h2>{imageArticles[2].headline.main}</h2>
        <p>{imageArticles[2].abstract}</p>
        <p>{imageArticles[2].lead_paragraph}</p>
        <hr style="margin: 5% 0% 10% 0%"/>

        <img src={getImage(imageArticles[3])} alt={imageArticles[3].headline.main}/>
        <h2>{imageArticles[3].headline.main}</h2>
        <p>{imageArticles[3].abstract}</p>
        <p>{imageArticles[3].lead_paragraph}</p>
        <hr style="margin: 5% 0% 10% 0%"/>

        <img src={getImage(imageArticles[5])} alt={imageArticles[5].headline.main}/>
        <h2>{imageArticles[5].headline.main}</h2>
        <p>{imageArticles[5].abstract}</p>
        <p>{imageArticles[5].lead_paragraph}</p>
        <hr style="margin: 5% 0% 10% 0%"/>

        <img src={getImage(imageArticles[7])} alt={imageArticles[7].headline.main}/>
        <h2>{imageArticles[7].headline.main}</h2>
        <p>{imageArticles[7].abstract}</p>
        <p>{imageArticles[7].lead_paragraph}</p>
      </div>
    </div>
  {:else}
    <p>Loading articles...</p>
  {/if}
  <hr style="height: 3px; background-color: black; margin: 2% 2% 3% 2%" />
</main>
<!-- <script lang="ts">
  import { onMount } from 'svelte';

  let today = '';                       
  let articles: any[] = [];              
  let imageArticles: any[] = [];          
  let error = '';                     
  let apiKey = '';                        

  function getImage(article: any): string | null {
    if (article?.multimedia?.default?.url) {
      return article.multimedia.default.url;
    } else if (article?.multimedia?.thumbnail?.url) {
      return article.multimedia.thumbnail.url;
    }
    return null;
  }

  onMount(async () => {
    const now = new Date();
    today = now.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });

    try {
      const res = await fetch('/api/local-news');
      const data = await res.json();
      articles       = data.response?.docs || [];
      imageArticles  = articles.filter(a => getImage(a));
    } catch (e) {
      error = 'Failed to load articles';
      console.error(e);
    }

    try {
      const res = await fetch('/api/key');
      const data = await res.json();
      apiKey = data.apiKey;
    } catch (e) {
      error = 'Failed to load API key';
      console.error(e);
    }
  });
</script>

<main>
  <header>
    <div class="date">
      <p><b>{today}</b><br/>Today’s Paper</p>
    </div>

    <br>
    <br>

    <div class="logo-image">
      <img src="/NYTimeslogo.png" alt="The New York Times" />
    </div>


    <nav style="margin: 10px 0;">
      <a href="/login">Login</a> |
      <a href="/logout">Logout</a>
    </nav>

    <hr style="margin: 1% 2%; width: 95%" />
  </header>

  {#if error}
    <p>{error}</p>
  {:else if imageArticles.length === 0}
    <p>Loading articles…</p>
  {:else}
    <div class="main-container">
      <div class="left-column">
        {#each [2,3] as idx}
          <article>
            <img src={getImage(imageArticles[idx])}
                 alt={imageArticles[idx].headline.main}/>
            <h2>{imageArticles[idx].headline.main}</h2>
            <p>{imageArticles[idx].abstract}</p>
            <p>{imageArticles[idx].lead_paragraph}</p>
            {#if idx === 2}<hr style="margin:2% 0 10% 0"/>{/if}
          </article>
        {/each}
      </div>

      <div class="mid-column">
        <article>
          <img src={getImage(imageArticles[0])}
               alt={imageArticles[0].headline.main}/>
          <h1>{imageArticles[0].headline.main}</h1>
          <p>{imageArticles[0].abstract}</p>
          <p>{imageArticles[0].lead_paragraph}</p>
        </article>

        <hr style="margin:1% 0 5% 0"/>

        <article>
          <img src={getImage(imageArticles[1])}
               alt={imageArticles[1].headline.main}/>
          <h3>{imageArticles[1].headline.main}</h3>
          <p>{imageArticles[1].abstract}</p>
          <p>{imageArticles[1].lead_paragraph}</p>
        </article>
      </div>

      <div class="right-column">
        {#each [5,7] as idx}
          <article>
            <img src={getImage(imageArticles[idx])}
                 alt={imageArticles[idx].headline.main}/>
            <h2>{imageArticles[idx].headline.main}</h2>
            <p>{imageArticles[idx].abstract}</p>
            <p>{imageArticles[idx].lead_paragraph}</p>
            {#if idx === 5}<hr style="margin:2% 0 10% 0"/>{/if}
          </article>
        {/each}
      </div>

      <div class="side-columns">
        {#each [2,3,5,7] as idx}
          <article>
            <img src={getImage(imageArticles[idx])}
                 alt={imageArticles[idx].headline.main}/>
            <h2>{imageArticles[idx].headline.main}</h2>
            <p>{imageArticles[idx].abstract}</p>
            <p>{imageArticles[idx].lead_paragraph}</p>
            <hr style="margin:5% 0 10% 0"/>
          </article>
        {/each}
      </div>
    </div>
  {/if}

  <hr style="height:3px; background:#000; margin:2% 2% 3%"/>
</main> -->
