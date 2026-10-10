import React from 'react';
interface CardProps{
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;

};

export const Card: React.FC<CardProps> = ({ children, className = '' }) => {
    return (
        <div className={`bg-white border border-slate-200 rounded-xl p-6 shadow-sm ${className}`}>
      {children}
    </div>
    );
};