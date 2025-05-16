<script lang="ts">
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
      <!-- LEFT COLUMN -->
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

      <!-- MIDDLE COLUMN -->
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

      <!-- RIGHT COLUMN -->
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

      <!-- SIDE COLUMNS (mobile / extra) -->
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
</main>
