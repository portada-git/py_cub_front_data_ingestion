import React, { useState } from "react";
import {
  Upload,
  AlertCircle,
  Loader2,
  Play,
  FileText,
  ChevronDown,
  CheckCircle,
  XCircle,
  Newspaper,
} from "lucide-react";
import { useStore } from "../store/useStore";
import { clsx } from "clsx";
import type { AnalysisResult } from "../types";
import newspapersData from "../data/newspapers.json";

type IngestionType = "extraction" | "known_entities";

interface Newspaper {
  id: string;
  name: string;
  code: string;
  description: string;
}

const IngestionView: React.FC = () => {
  const { setIsProcessing, setAnalysisResult, isProcessing } = useStore();

  const [ingestionType, setIngestionType] = useState<IngestionType>("extraction");
  const [selectedNewspaper, setSelectedNewspaper] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");

  const newspapers: Newspaper[] = newspapersData.newspapers;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    
    if (!selectedFile) return;

    // Validar tipo de archivo según el tipo de ingestión
    const validExtensions = ingestionType === "extraction" 
      ? [".json", ".yml", ".yaml"]
      : [".json", ".yml", ".yaml"];
    
    const isValidFile = validExtensions.some(ext => 
      selectedFile.name.toLowerCase().endsWith(ext)
    );

    if (!isValidFile) {
      setUploadStatus("error");
      alert(`Por favor, selecciona un archivo válido (${validExtensions.join(", ")})`);
      return;
    }

    setFile(selectedFile);
    simulateUpload();
  };

  const simulateUpload = () => {
    setUploadStatus("uploading");
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadProgress(progress);
      if (progress >= 100) {
        clearInterval(interval);
        setUploadStatus("success");
      }
    }, 100);
  };

  const handleProcess = async () => {
    if (!file) return;
    
    // Validate newspaper selection for extraction type
    if (ingestionType === "extraction" && !selectedNewspaper) {
      alert("Por favor, selecciona un periódico antes de procesar.");
      return;
    }

    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("ingestion_type", ingestionType);
      
      // Add newspaper parameter for extraction type
      if (ingestionType === "extraction" && selectedNewspaper) {
        formData.append("newspaper", selectedNewspaper);
      }

      const response = await fetch("http://localhost:8000/api/ingestion/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const result = await response.json();
      
      setIsProcessing(false);
      alert(`Datos procesados con éxito. Task ID: ${result.task_id}\nDirígete a la pestaña de Análisis.`);
      
      // Reset form
      setFile(null);
      setUploadStatus("idle");
      setUploadProgress(0);
      if (ingestionType === "extraction") {
        setSelectedNewspaper("");
      }
      
    } catch (error) {
      setIsProcessing(false);
      alert(`Error al procesar los datos: ${error instanceof Error ? error.message : 'Error desconocido'}`);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Ingestion Type Selection */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">Tipo de Carga de Datos</h2>
        <div className="relative">
          <select
            value={ingestionType}
            onChange={(e) => setIngestionType(e.target.value as IngestionType)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none cursor-pointer"
          >
            <option value="extraction">Extracción</option>
            <option value="known_entities">Entidades Conocidas</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
        </div>
        <p className="text-slate-400 text-sm mt-2">
          {ingestionType === "extraction" 
            ? "Carga de datos de extracción desde archivos JSON/YAML"
            : "Carga de entidades conocidas desde archivos JSON/YAML"
          }
        </p>
      </div>

      {/* Newspaper Selection - Only for extraction type */}
      {ingestionType === "extraction" && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-indigo-500/10 rounded-lg">
              <Newspaper className="w-6 h-6 text-indigo-400" />
            </div>
            <h2 className="text-xl font-bold text-white">Periódico</h2>
          </div>
          <div className="relative">
            <select
              value={selectedNewspaper}
              onChange={(e) => setSelectedNewspaper(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none cursor-pointer"
              required
            >
              <option value="">Selecciona el periódico de origen</option>
              {newspapers.map((newspaper) => (
                <option key={newspaper.id} value={newspaper.id}>
                  {newspaper.name} ({newspaper.code})
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
          </div>
          {selectedNewspaper && (
            <p className="text-slate-400 text-sm mt-2">
              {newspapers.find(n => n.id === selectedNewspaper)?.description}
            </p>
          )}
        </div>
      )}

      {/* File Upload Zone */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 rounded-xl">
            <FileText className="w-8 h-8 text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">
              {ingestionType === "extraction" ? "Datos de Extracción" : "Entidades Conocidas"}
            </h3>
            <p className="text-slate-400 text-sm">
              Archivos .json / .yml / .yaml
            </p>
          </div>
        </div>

        <label
          className={clsx(
            "flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl cursor-pointer transition-all",
            file
              ? "border-blue-500/50 bg-blue-500/5"
              : "border-slate-700 hover:border-slate-600 bg-slate-800/50"
          )}
        >
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            {uploadStatus === "success" ? (
              <CheckCircle className="w-10 h-10 mb-3 text-green-400" />
            ) : uploadStatus === "error" ? (
              <XCircle className="w-10 h-10 mb-3 text-red-400" />
            ) : uploadStatus === "uploading" ? (
              <Loader2 className="w-10 h-10 mb-3 text-blue-400 animate-spin" />
            ) : (
              <Upload
                className={clsx(
                  "w-10 h-10 mb-3",
                  file ? "text-blue-400" : "text-slate-500"
                )}
              />
            )}
            <p className="mb-2 text-sm text-slate-300">
              <span className="font-semibold">Click para subir</span> o
              arrastra y suelta
            </p>
          </div>
          <input
            type="file"
            className="hidden"
            accept=".json,.yml,.yaml"
            onChange={handleFileChange}
          />
        </label>

        {file && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-300 truncate max-w-[200px]">
                {file.name}
              </span>
              <span className={clsx(
                "font-medium",
                uploadStatus === "success" ? "text-green-400" : 
                uploadStatus === "error" ? "text-red-400" : "text-blue-400"
              )}>
                {uploadStatus === "success" ? "Completado" :
                 uploadStatus === "error" ? "Error" : `${uploadProgress}%`}
              </span>
            </div>
            {uploadStatus === "uploading" && (
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex justify-center pt-4">
        <button
          onClick={handleProcess}
          disabled={
            !file || 
            uploadStatus !== "success" || 
            isProcessing ||
            (ingestionType === "extraction" && !selectedNewspaper)
          }
          className={clsx(
            "flex items-center gap-3 px-10 py-4 rounded-xl font-bold text-lg transition-all shadow-lg",
            !file || 
            uploadStatus !== "success" || 
            isProcessing ||
            (ingestionType === "extraction" && !selectedNewspaper)
              ? "bg-slate-800 text-slate-500 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-500 hover:shadow-blue-500/20 active:scale-95"
          )}
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              <span>Procesando Datos...</span>
            </>
          ) : (
            <>
              <Play className="w-6 h-6 fill-current" />
              <span>Procesar Datos</span>
            </>
          )}
        </button>
      </div>

      {/* Info Card */}
      <div className="bg-blue-900/10 border border-blue-800/30 rounded-xl p-6 flex gap-4 items-start">
        <AlertCircle className="w-6 h-6 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-sm text-slate-400 leading-relaxed">
          <p className="text-blue-200 font-medium mb-1">
            Instrucciones de Carga
          </p>
          El proceso de ingestión es asíncrono. Una vez subido el archivo, 
          recibirás una confirmación inmediata, pero el procesamiento continuará 
          en segundo plano. Los resultados estarán disponibles en la sección de Análisis.
        </div>
      </div>
    </div>
  );
};

export default IngestionView;
