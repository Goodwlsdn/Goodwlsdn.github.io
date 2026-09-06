const posts = [
  {
    title: "행안부 게시판 모니터링 만들기",
    tag: "Automation",
    date: "2026.09",
    summary:
      "Python으로 공공기관 게시판을 확인하고 새 글을 감지하는 작은 자동화 프로젝트.",
  },
  {
    title: "블로그 개발 환경 만들기",
    tag: "Web",
    date: "2026.09",
    summary:
      "GitHub Pages로 운영할 개인 블로그 레포를 만들고 로컬 개발 흐름을 정리한다.",
  },
  {
    title: "데이터 수집 공부 로드맵",
    tag: "Data",
    date: "Soon",
    summary:
      "requests, BeautifulSoup, pandas를 거쳐 분석 노트북까지 이어지는 학습 기록.",
  },
];

const projects = [
  "mois-board-monitor",
  "blog",
  "data-analysis",
  "scraping-labs",
];

export default function Home() {
  return (
    <main>
      <section className="hero">
        <div className="hero__content">
          <p className="eyebrow">Goodwlsdn.github.io</p>
          <h1>만들면서 배우는 개발 기록</h1>
          <p className="hero__lead">
            블로그, 자동화, 데이터 수집, 분석 프로젝트를 하나씩 만들고 남기는
            개인 개발 노트입니다.
          </p>
          <div className="hero__actions" aria-label="Primary sections">
            <a href="#posts">글 보기</a>
            <a href="#projects">프로젝트</a>
          </div>
        </div>
        <div className="hero__panel" aria-label="Current workspace snapshot">
          <div className="panel__topline">
            <span>workspace</span>
            <strong>4 repos planned</strong>
          </div>
          <div className="terminal-card">
            <p>$ git clone Goodwlsdn/mois-board-monitor</p>
            <p>$ mkdir Goodwlsdn.github.io</p>
            <p>$ pnpm dev</p>
          </div>
        </div>
      </section>

      <section className="section" id="posts">
        <div className="section__header">
          <p className="eyebrow">Latest Notes</p>
          <h2>최근 기록</h2>
        </div>
        <div className="post-grid">
          {posts.map((post) => (
            <article className="post-card" key={post.title}>
              <div className="post-card__meta">
                <span>{post.tag}</span>
                <time>{post.date}</time>
              </div>
              <h3>{post.title}</h3>
              <p>{post.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section section--split" id="projects">
        <div>
          <p className="eyebrow">Build Log</p>
          <h2>앞으로 만들 저장소들</h2>
          <p>
            각 프로젝트는 독립된 레포로 관리하고, 블로그에는 만든 과정과
            배운 점을 짧게 정리하는 방식으로 쌓아갑니다.
          </p>
        </div>
        <ul className="repo-list">
          {projects.map((project) => (
            <li key={project}>
              <span>{project}</span>
              <small>repo</small>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
