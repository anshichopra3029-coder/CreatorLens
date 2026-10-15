import { useParams } from "react-router-dom";
import { YoutubeResults } from "../components/youtube/YoutubeResults.tsx";

export function YoutubeAnalysisPage() {
  const { analysisId } = useParams();
  if (!analysisId) {
    return <p className="text-sm text-slate-600">Choose a saved YouTube analysis.</p>;
  }
  return <YoutubeResults analysisId={analysisId} />;
}