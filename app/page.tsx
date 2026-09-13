const posts = [
  {
    title: "지도에서 개발로 이어지는 기록",
    tag: "Intro",
    date: "2026.09",
    summary:
      "지리학을 공부하고 차량 인포테인먼트 지도 업무를 하며 느낀 개발 공부의 필요성을 적어갑니다.",
  },
  {
    title: "업무를 더 잘 이해하기 위한 IT 공부",
    tag: "Study",
    date: "2026.09",
    summary:
      "소프트웨어, 데이터, 자동화 지식을 차근차근 익히고 실제로 만들어보는 과정을 남깁니다.",
  },
  {
    title: "데이터 수집과 분석으로 넓히기",
    tag: "Data",
    date: "Soon",
    summary:
      "공공데이터, 웹 데이터, 지도 데이터를 수집하고 분석하는 작은 실험들을 정리할 예정입니다.",
  },
];

const profile = [
  ["Education", "경희대학교 지리학과 졸업"],
  ["Experience", "현대오토에버 인포테인먼트SW사업부 재직"],
  ["Focus", "지도 개발, 내비게이션, 데이터, SW/IT 학습"],
];

export default function Home() {
  return (
    <main>
      <section className="hero">
        <div className="hero__content">
          <p className="eyebrow">Goodwlsdn</p>
          <h1>지도와 데이터를 공부하는 SW 실무자</h1>
          <p className="hero__lead">
            안녕하세요. 지리학을 전공하며 지도에 대한 막연한 관심으로
            시작해, 지금은 현대자동차 내비게이션에 탑재되는 지도를 개발하는
            업무를 하고 있습니다. SW/데이터 비전공자로서 개발 및 IT 지식이
            많이 부족하다고 느껴, 공부하고 만들어보는 과정을 꾸준히 기록하고자
            합니다.
          </p>
        </div>
        <div className="hero__panel" aria-label="Profile summary">
          <div className="panel__topline">
            <span>Profile</span>
          </div>
          <div className="profile-head">
            <div className="avatar" aria-hidden="true">G</div>
            <div>
              <h2>Goodwlsdn</h2>
              <p>Navigation Map Developer</p>
            </div>
          </div>
          <dl className="profile-list">
            {profile.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="section section--intro" id="profile">
        <p className="eyebrow">About</p>
        <h2>왜 기록하나요</h2>
        <p>
          지리학에서 출발해 지도와 위치 정보를 다루는 일을 하고 있지만,
          서비스를 더 깊이 이해하고 직접 만들기 위해서는 개발 기반이 필요하다고
          느꼈습니다. 이곳에는 공부한 개념, 막혔던 부분, 직접 만든 작은 도구와
          데이터 분석 과정을 꾸준히 남깁니다.
        </p>
      </section>

      <section className="section" id="posts">
        <div className="section__header">
          <p className="eyebrow">Study Notes</p>
          <h2>앞으로 쌓아갈 기록</h2>
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

      <section className="section section--split">
        <div>
          <p className="eyebrow">Next</p>
          <h2>만들면서 배우기</h2>
          <p>
            블로그를 시작점으로 삼아 데이터 수집, 분석, 자동화, 웹 개발을
            하나씩 실습합니다. 완성된 결과보다 과정을 남기는 데 초점을 둡니다.
          </p>
        </div>
        <div className="focus-box">
          <span>01</span>
          <p>지도와 위치 데이터를 더 잘 이해하기</p>
          <span>02</span>
          <p>업무에 필요한 개발/IT 개념 정리하기</p>
          <span>03</span>
          <p>데이터 수집과 분석 프로젝트 만들기</p>
        </div>
      </section>
    </main>
  );
}
