import React, { useMemo, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { ConceptNode } from '../../types';
import type { ApiConcept } from '../../api/types';

// Before the quiz no mastery is known: concepts the notes cover are 'unassessed';
// background knowledge the notes rely on (source_type 'inferred') is shown as 'prerequisite'.
const toNode = (c: ApiConcept): ConceptNode => ({
  id: c.id,
  label: c.name,
  status: c.source_type === 'inferred' ? 'prerequisite' : 'unassessed',
  description: c.description,
});

export const KnowledgeGraph: React.FC = () => {
  const { setStep, analysis } = useApp();
  const [selectedNode, setSelectedNode] = useState<ConceptNode | null>(null);

  const concepts = analysis?.concepts ?? [];
  const nodes = useMemo(() => concepts.map(toNode), [concepts]);
  const conceptById = useMemo(() => new Map(concepts.map((c) => [c.id, c])), [concepts]);
  const selectedConcept = selectedNode ? conceptById.get(selectedNode.id) : undefined;

  if (!analysis) {
    return (
      <div className="max-w-5xl mx-auto p-6 text-center">
        <p className="text-gray-600 mb-4">No document has been analyzed yet.</p>
        <button onClick={() => setStep('upload')} className="bg-blue-600 text-white px-4 py-2 rounded-md">
          Upload a Document
        </button>
      </div>
    );
  }

  const getStatusColor = (status: ConceptNode['status']) => {
    switch (status) {
      case 'mastered': return 'bg-green-100 border-green-500 text-green-800';
      case 'gap': return 'bg-red-100 border-red-500 text-red-800';
      case 'prerequisite': return 'bg-blue-100 border-blue-500 text-blue-800';
      case 'unassessed': return 'bg-gray-100 border-gray-400 text-gray-800';
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Concept Knowledge Graph</h2>
          <p className="text-gray-600 text-sm">
            {analysis.document_name} &middot; {concepts.length} concepts. Click on a concept node to view details.
          </p>
        </div>
        <button
          onClick={() => setStep('quiz')}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
        >
          Take Assessment Quiz &rarr;
        </button>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mb-6 text-sm">
        <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-green-500" /> Mastered</span>
        <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-500" /> Knowledge Gap</span>
        <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-blue-500" /> Prerequisite</span>
        <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-gray-400" /> Not yet assessed</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Graph Visual Grid */}
        <div className="md:col-span-2 border rounded-xl p-6 bg-white shadow-sm min-h-[350px] flex flex-wrap gap-4 items-center justify-center">
          {nodes.map((node) => (
            <button
              key={node.id}
              onClick={() => setSelectedNode(node)}
              className={`p-4 rounded-lg border-2 font-medium cursor-pointer transition shadow-sm hover:scale-105 ${getStatusColor(node.status)}`}
            >
              {node.label}
            </button>
          ))}
        </div>

        {/* Node Sidebar Details */}
        <div className="border rounded-xl p-6 bg-white shadow-sm">
          <h3 className="font-semibold text-lg border-b pb-2 mb-3">Concept Details</h3>
          {selectedNode ? (
            <div>
              <h4 className="font-bold text-gray-900">{selectedNode.label}</h4>
              <span className={`inline-block my-2 px-2 py-0.5 text-xs font-semibold rounded uppercase ${getStatusColor(selectedNode.status)}`}>
                {selectedNode.status}
              </span>
              <p className="text-sm text-gray-600 mt-2">{selectedNode.description}</p>
              {selectedConcept && (
                <dl className="text-sm text-gray-700 mt-4 space-y-2">
                  <div>
                    <dt className="font-semibold">Difficulty</dt>
                    <dd className="capitalize">{selectedConcept.difficulty}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold">Requires</dt>
                    <dd>
                      {selectedConcept.prerequisites.length
                        ? selectedConcept.prerequisites.map((id) => conceptById.get(id)?.name ?? id).join(', ')
                        : 'None (foundational concept)'}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold">Concepts that build on it</dt>
                    <dd>{selectedConcept.descendant_count}</dd>
                  </div>
                </dl>
              )}
            </div>
          ) : (
            <p className="text-gray-400 text-sm italic">Select a node to inspect concept gaps.</p>
          )}
        </div>
      </div>
    </div>
  );
};