import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { ConceptNode } from '../../types';

const mockNodes: ConceptNode[] = [
  { id: '1', label: 'Linear Algebra', status: 'mastered', description: 'Vectors, matrices, and basic linear transformations.' },
  { id: '2', label: 'Matrix Multiplication', status: 'mastered', description: 'Dot product of rows and columns.' },
  { id: '3', label: 'Eigenvalues & Eigenvectors', status: 'gap', description: 'Characteristic equations and scalar transformations. Needs review!' },
  { id: '4', label: 'Principal Component Analysis (PCA)', status: 'prerequisite', description: 'Dimensionality reduction technique relying on Eigenvectors.' },
];

export const KnowledgeGraph: React.FC = () => {
  const { setStep } = useApp();
  const [selectedNode, setSelectedNode] = useState<ConceptNode | null>(null);

  const getStatusColor = (status: ConceptNode['status']) => {
    switch (status) {
      case 'mastered': return 'bg-green-100 border-green-500 text-green-800';
      case 'gap': return 'bg-red-100 border-red-500 text-red-800';
      case 'prerequisite': return 'bg-blue-100 border-blue-500 text-blue-800';
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Concept Knowledge Graph</h2>
          <p className="text-gray-600 text-sm">Click on a concept node to view gap details.</p>
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
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Graph Visual Grid */}
        <div className="md:col-span-2 border rounded-xl p-6 bg-white shadow-sm min-h-[350px] flex flex-wrap gap-4 items-center justify-center">
          {mockNodes.map((node) => (
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
            </div>
          ) : (
            <p className="text-gray-400 text-sm italic">Select a node to inspect concept gaps.</p>
          )}
        </div>
      </div>
    </div>
  );
};