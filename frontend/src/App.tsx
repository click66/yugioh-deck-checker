import React, { useState } from "react";
import { createJob, getJob } from "./services/consistency";
import type { ConsistencyJobResponse } from "./services/consistency";

type DeckLine = { count: number; name: string };

export default function App() {
  const [expandedSteps, setExpandedSteps] = useState<{ [key: number]: boolean }>({
    1: true,
    2: false,
    3: false,
  });

  // Step 1
  const [deckText, setDeckText] = useState("");
  const [deck, setDeck] = useState<DeckLine[]>([]);

  // Step 2
  const [hands, setHands] = useState<string[][]>([]);
  const [showHandModal, setShowHandModal] = useState(false);
  const [newHand, setNewHand] = useState<string[]>([]);

  // Step 3
  const [job, setJob] = useState<ConsistencyJobResponse | null>(null);
  const [loading, setLoading] = useState(false);

  // --- Step 1 logic ---
  const parseDeck = () => {
    const lines = deckText
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    const parsed: DeckLine[] = [];
    for (const line of lines) {
      const match = line.match(/^(\d+)\s+(.+)$/);
      if (match) {
        parsed.push({ count: Number(match[1]), name: match[2].trim() });
      }
    }
    setDeck(parsed);

    // Clear existing hands and reset job if deck changed
    setHands([]);
    setJob(null);

    // Collapse Step 1, expand Step 2
    setExpandedSteps((prev) => ({ ...prev, 1: false, 2: true }));
  };

  // --- Step 2 logic ---
  const addHand = () => {
    if (newHand.length > 0) {
      setHands([...hands, newHand]);
      setNewHand([]);
      setShowHandModal(false);
      // Step 2 stays expanded; Step 3 expands
      setExpandedSteps((prev) => ({ ...prev, 3: true }));
    }
  };

  // --- Step 3 logic ---
  const runAnalysis = async () => {
    if (deck.length === 0) return;
    setLoading(true);

    const names = deck.map((d) => d.name);
    const ratios = deck.map((d) => d.count);

    const payload = {
      deckcount: 40,
      names,
      ratios,
      ideal_hands: hands,
      num_hands: hands.length,
    };

    try {
      const jobResp = await createJob(payload);
      setJob(jobResp);

      const poll = async () => {
        if (!jobResp.jobId) return;
        const result = await getJob(jobResp.jobId);
        setJob(result);
        if (result.status !== "done") {
          setTimeout(poll, 5000);
        }
      };
      poll();
    } finally {
      setLoading(false);
    }
  };

  const toggleStep = (step: number) => {
    setExpandedSteps((prev) => ({ ...prev, [step]: !prev[step] }));
  };

  return (
    <div className="p-4 space-y-4 max-w-3xl mx-auto">
      <Step1
        expanded={expandedSteps[1]}
        toggle={() => toggleStep(1)}
        deckText={deckText}
        setDeckText={setDeckText}
        parseDeck={parseDeck}
      />
      <Step2
        expanded={expandedSteps[2]}
        toggle={() => toggleStep(2)}
        deck={deck}
        hands={hands}
        showHandModal={showHandModal}
        setShowHandModal={setShowHandModal}
        newHand={newHand}
        setNewHand={setNewHand}
        addHand={addHand}
      />
      <Step3
        expanded={expandedSteps[3]}
        toggle={() => toggleStep(3)}
        deck={deck}
        hands={hands}
        runAnalysis={runAnalysis}
        loading={loading}
        job={job}
      />
    </div>
  );
}

// ---------------- Step 1 ----------------
type Step1Props = {
  expanded: boolean;
  toggle: () => void;
  deckText: string;
  setDeckText: React.Dispatch<React.SetStateAction<string>>;
  parseDeck: () => void;
};
function Step1({ expanded, toggle, deckText, setDeckText, parseDeck }: Step1Props) {
  return (
    <div className="border rounded shadow p-4">
      <h2 className="font-bold cursor-pointer" onClick={toggle}>
        Step 1: Deck Selection
      </h2>
      {expanded && (
        <div className="mt-2">
          <textarea
            className="w-full border p-2"
            rows={10}
            value={deckText}
            onChange={(e) => setDeckText(e.target.value)}
            placeholder="Enter deck list..."
          />
          <button
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
            onClick={parseDeck}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------- Step 2 ----------------
type Step2Props = {
  expanded: boolean;
  toggle: () => void;
  deck: DeckLine[];
  hands: string[][];
  showHandModal: boolean;
  setShowHandModal: React.Dispatch<React.SetStateAction<boolean>>;
  newHand: string[];
  setNewHand: React.Dispatch<React.SetStateAction<string[]>>;
  addHand: () => void;
};
function Step2({
  expanded,
  toggle,
  deck,
  hands,
  showHandModal,
  setShowHandModal,
  newHand,
  setNewHand,
  addHand,
}: Step2Props) {
  return (
    <div className="border rounded shadow p-4">
      <h2 className="font-bold cursor-pointer" onClick={toggle}>
        Step 2: Ideal Hand Selection
      </h2>
      {expanded && (
        <div className="mt-2">
          <button
            className="mb-2 px-4 py-2 bg-green-500 text-white rounded"
            onClick={() => setShowHandModal(true)}
          >
            Add New Hand
          </button>
          <ul className="space-y-1">
            {hands.map((hand, idx) => (
              <li key={idx} className="border p-2 rounded">
                {hand.join(", ")}
              </li>
            ))}
          </ul>

          {showHandModal && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
              <div className="bg-white p-6 rounded max-w-2xl w-full">
                <h3 className="font-bold mb-2">Select Cards</h3>
                <div className="grid grid-cols-2 gap-2 max-h-80 overflow-y-auto">
                  {deck.map((d) => (
                    <label
                      key={d.name}
                      className="flex items-center space-x-2 border p-1 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={newHand.includes(d.name)}
                        onChange={(e) => {
                          if (e.target.checked) setNewHand([...newHand, d.name]);
                          else setNewHand(newHand.filter((n) => n !== d.name));
                        }}
                      />
                      <span>{d.name}</span>
                    </label>
                  ))}
                </div>
                <div className="mt-4 flex justify-end space-x-2">
                  <button
                    className="px-3 py-1 bg-gray-300 rounded"
                    onClick={() => setShowHandModal(false)}
                  >
                    Cancel
                  </button>
                  <button
                    className="px-3 py-1 bg-blue-500 text-white rounded"
                    onClick={addHand}
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------- Step 3 ----------------
type Step3Props = {
  expanded: boolean;
  toggle: () => void;
  deck: DeckLine[];
  hands: string[][];
  runAnalysis: () => void;
  loading: boolean;
  job: ConsistencyJobResponse | null;
};
function Step3({ expanded, toggle, deck, hands, runAnalysis, loading, job }: Step3Props) {
  return (
    <div className="border rounded shadow p-4">
      <h2 className="font-bold cursor-pointer" onClick={toggle}>
        Step 3: Run Analysis
      </h2>
      {expanded && (
        <div className="mt-2">
          <button
            className="px-4 py-2 bg-purple-500 text-white rounded flex items-center space-x-2"
            onClick={runAnalysis}
            disabled={loading}
          >
            {loading && (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            )}
            <span>{loading ? "Running" : "Run Analysis"}</span>
          </button>

          {job && (
            <div className="mt-2">
              <p>Status: {job.status}</p>
              {job.result && (
                <pre className="bg-gray-100 p-2 rounded">{JSON.stringify(job.result, null, 2)}</pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}