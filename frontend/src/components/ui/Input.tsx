import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  icon,
  className = "",
  id,
  ...props
}) => {
  const inputId = id || `input-${Date.now()}`;

  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-text-primary">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <div className="h-5 w-5 text-text-secondary">
              {icon}
            </div>
          </div>
        )}
        <input
          id={inputId}
          className={`
            block w-full rounded-lg border border-border bg-surface px-3 py-2 text-text-primary 
            placeholder-text-secondary focus:border-primary focus:outline-none focus:ring-2 
            focus:ring-primary focus:ring-opacity-20 disabled:opacity-50 disabled:cursor-not-allowed
            ${icon ? "pl-10" : ""}
            ${error ? "border-error focus:border-error focus:ring-error" : ""}
            ${className}
          `}
          {...props}
        />
      </div>
      {error && (
        <p className="text-sm text-error">{error}</p>
      )}
    </div>
  );
};

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  className = "",
  id,
  ...props
}) => {
  const textareaId = id || `textarea-${Date.now()}`;

  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={textareaId} className="block text-sm font-medium text-text-primary">
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        className={`
          block w-full rounded-lg border border-border bg-surface px-3 py-2 text-text-primary 
          placeholder-text-secondary focus:border-primary focus:outline-none focus:ring-2 
          focus:ring-primary focus:ring-opacity-20 disabled:opacity-50 disabled:cursor-not-allowed
          resize-vertical
          ${error ? "border-error focus:border-error focus:ring-error" : ""}
          ${className}
        `}
        {...props}
      />
      {error && (
        <p className="text-sm text-error">{error}</p>
      )}
    </div>
  );
};
