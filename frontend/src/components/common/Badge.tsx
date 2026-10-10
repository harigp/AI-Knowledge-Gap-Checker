import React from 'react';
interface BadgeProps{
    children: React.ReactNode;
    variant?: 'green' | 'red' | 'yellow'|'gray';
};

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'gray' }) => {
    const variantClasses = {
        green: 'bg-green-100 text-green-800 border border-green-200',
        red: 'bg-red-100 text-red-800 border border-red-200',
        yellow: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
        gray: 'bg-gray-100 text-gray-800 border border-gray-200'
    };

    return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variantClasses[variant]}`}>
      {children}
    </span>
    );
};
