import { useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { createRoot } from "react-dom/client";
import "./styles.css";

const config = {
  url: import.meta.env.VITE_SUPABASE_URL,
  anonKey: import.meta.env.VITE_SUPABASE_ANON_KEY,
  apiUrl: import.meta.env.VITE_RENDER_API_URL,
};
const supabase = config.url && config.anonKey ? createClient(config.url, config.anonKey) : null;

function App() {
  const [session, setSession] = useState(null);
  const [email, setEmail] = useState("");
  const [title, setTitle] = useState("");
  const [audience, setAudience] = useState("초등학교 5학년");
  const [duration, setDuration] = useState(70);
  const [files, setFiles] = useState([]);
  const [job, setJob] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: listener } = supabase.auth.onAuthStateChange((_, next) => setSession(next));
    return () => listener.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!job || !session || ["passed", "needs_user_review", "failed"].includes(job.status)) return;
    const timer = setInterval(() => refreshJob(job.id, session.access_token), 3000);
    return () => clearInterval(timer);
  }, [job?.id, job?.status, session?.access_token]);

  const ready = useMemo(() => session && title.trim() && files.length && config.apiUrl, [session, title, files]);

  async function signIn(event) {
    event.preventDefault();
    if (!supabase) return setMessage("Supabase 환경변수를 먼저 설정하세요.");
    const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: window.location.origin } });
    setMessage(error ? error.message : "로그인 링크를 이메일로 보냈습니다.");
  }

  async function submit(event) {
    event.preventDefault();
    if (!ready) return;
    try {
      setMessage("원본을 안전하게 업로드하는 중입니다.");
      const paths = [];
      for (const file of files) {
        const path = `${session.user.id}/${crypto.randomUUID()}-${file.name}`;
        const { error } = await supabase.storage.from("short-sources").upload(path, file, { upsert: false });
        if (error) throw error;
        paths.push(path);
      }
      const response = await fetch(`${config.apiUrl}/v1/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${session.access_token}` },
        body: JSON.stringify({ title, audience, duration: Number(duration), source_paths: paths }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "작업을 시작하지 못했습니다.");
      setJob(data);
      setMessage("제작 작업을 시작했습니다.");
      refreshJob(data.job_id, session.access_token);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function refreshJob(id, token) {
    const response = await fetch(`${config.apiUrl}/v1/jobs/${id}`, { headers: { Authorization: `Bearer ${token}` } });
    if (response.ok) setJob(await response.json());
  }

  if (!config.url || !config.anonKey || !config.apiUrl) {
    return <main className="shell"><h1>Edu Shorts Studio</h1><p>웹 앱 환경변수를 설정하면 제작 화면이 열립니다.</p></main>;
  }
  return <main className="shell">
    <header><p className="eyebrow">EDUCATION VIDEO WORKFLOW</p><h1>교안을 70초의<br />배움으로 바꾸세요.</h1><p className="lede">원본은 보존하고, 근거가 확인된 쇼츠 제작안을 만듭니다.</p></header>
    {!session ? <form className="card" onSubmit={signIn}><h2>시작하기</h2><label>이메일<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label><button>로그인 링크 받기</button></form> :
      <form className="card" onSubmit={submit}><div className="form-head"><h2>새 쇼츠 만들기</h2><button type="button" className="quiet" onClick={() => supabase.auth.signOut()}>로그아웃</button></div><label>주제 제목<input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="예: 물의 순환" required /></label><div className="grid"><label>학습 대상<input value={audience} onChange={(e) => setAudience(e.target.value)} required /></label><label>길이<select value={duration} onChange={(e) => setDuration(e.target.value)}>{[60, 65, 70, 75].map((n) => <option key={n} value={n}>{n}초</option>)}</select></label></div><label className="drop">교안 파일<input type="file" multiple onChange={(e) => setFiles([...e.target.files])} accept=".pptx,.pdf,.docx,.hwp,.hwpx,.xlsx,.xls,.csv,.txt,.md,image/*,audio/*,video/*" /><span>{files.length ? `${files.length}개 파일 선택됨` : "PPTX, PDF, 문서, 표, 이미지, 음성 또는 영상을 선택하세요"}</span></label><button disabled={!ready}>제작 시작</button></form>}
    {message && <p className="message">{message}</p>}
    {job && <section className="status"><p className="eyebrow">CURRENT JOB</p><h2>{job.status === "queued" ? "대기 중" : job.status === "running" ? "제작 중" : job.status === "passed" ? "완료" : job.status}</h2><p>{job.error || "원자료 정리 → 분석 → 대본 → 장면 설계 → 독립 검수 순으로 진행합니다."}</p>{job.result_url && <a href={job.result_url}>제작 패키지 다운로드</a>}</section>}
  </main>;
}

createRoot(document.getElementById("root")).render(<App />);
