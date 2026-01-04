import React, { useState } from "react";
import {
  FileJson,
  FileCode,
  Upload,
  AlertCircle,
  Loader2,
  Play,
  FileText,
} from "lucide-react";
import { useStore } from "../store/useStore";
import { clsx } from "clsx";
import type { AnalysisResult } from "../types";
import yaml from "js-yaml";

const IngestionView: React.FC = () => {
  const { setIsProcessing, setAnalysisResult, isProcessing } = useStore();

  const [rawFile, setRawFile] = useState<File | null>(null);
  const [entityFile, setEntityFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<{
    raw: number;
    entity: number;
  }>({ raw: 0, entity: 0 });

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    type: "raw" | "entity"
  ) => {
    const file = e.target.files?.[0] || null;
    if (type === "raw") {
      if (
        file &&
        !file.name.endsWith(".json") &&
        !file.name.endsWith(".yml") &&
        !file.name.endsWith(".yaml")
      ) {
        alert("Por favor, selecciona un archivo .json o .yaml para Raw Data");
        return;
      }
      setRawFile(file);
      simulateUpload("raw");
    } else {
      if (
        file &&
        !file.name.endsWith(".json") &&
        !file.name.endsWith(".yml") &&
        !file.name.endsWith(".yaml")
      ) {
        alert(
          "Por favor, selecciona un archivo .json, .yml o .yaml para Entidades Conocidas"
        );
        return;
      }
      setEntityFile(file);
      simulateUpload("entity");
    }
  };

  const simulateUpload = (type: "raw" | "entity") => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadProgress((prev) => ({ ...prev, [type]: progress }));
      if (progress >= 100) clearInterval(interval);
    }, 100);
  };

  const handleProcess = () => {
    if (!rawFile || !entityFile) return;

    setIsProcessing(true);

    // Nota: Para archivos YAML muy grandes, se recomienda usar un Web Worker
    // para no bloquear el hilo principal de la UI durante el parseo.

    // Simulación de llamada a FastAPI
    setTimeout(() => {
      const mockResult: AnalysisResult = {
        metrics: {
          totalRecords: 1250,
          detectedEntities: 48,
          errors: 3,
        },
        missingDates: [
          { date: "2023-10-12", gap: "24h" },
          { date: "2023-10-15", gap: "12h" },
          { date: "2023-11-02", gap: "48h" },
        ],
        metadata: [
          { id: "1", key: "version", value: "2.4.0", source: "raw_header" },
          {
            id: "2",
            key: "environment",
            value: "production",
            source: "config_yml",
          },
          {
            id: "3",
            key: "region",
            value: "eu-west-1",
            source: "metadata_ext",
          },
        ],
        knownEntities: [
          {
            id: "e1",
            name: "Sensor_Alpha_01",
            type: "IoT_Device",
            linkedTo: ["Zone_A", "Gateway_01"],
          },
          {
            id: "e2",
            name: "User_Admin_Global",
            type: "Identity",
            linkedTo: ["Auth_Service"],
          },
          {
            id: "e3",
            name: "Database_Cluster_Main",
            type: "Infrastructure",
            linkedTo: ["AWS_RDS"],
          },
        ],
      };

      setAnalysisResult(mockResult);
      setIsProcessing(false);
      alert("Datos procesados con éxito. Dirígete a la pestaña de Análisis.");
    }, 2000);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Raw Data Zone */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 rounded-xl">
              <FileText className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Raw Data</h3>
              <p className="text-slate-400 text-sm">
                Archivos .json / .yml / .yaml
              </p>
            </div>
          </div>

          <label
            className={clsx(
              "flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl cursor-pointer transition-all",
              rawFile
                ? "border-blue-500/50 bg-blue-500/5"
                : "border-slate-700 hover:border-slate-600 bg-slate-800/50"
            )}
          >
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <Upload
                className={clsx(
                  "w-10 h-10 mb-3",
                  rawFile ? "text-blue-400" : "text-slate-500"
                )}
              />
              <p className="mb-2 text-sm text-slate-300">
                <span className="font-semibold">Click para subir</span> o
                arrastra y suelta
              </p>
            </div>
            <input
              type="file"
              className="hidden"
              accept=".json,.yml,.yaml"
              onChange={(e) => handleFileChange(e, "raw")}
            />
          </label>

          {rawFile && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-300 truncate max-w-[200px]">
                  {rawFile.name}
                </span>
                <span className="text-blue-400 font-medium">
                  {uploadProgress.raw}%
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress.raw}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* Known Entities Zone */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-indigo-500/10 rounded-xl">
              <FileCode className="w-8 h-8 text-indigo-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">
                Entidades Conocidas
              </h3>
              <p className="text-slate-400 text-sm">
                Archivos .json / .yml / .yaml
              </p>
            </div>
          </div>

          <label
            className={clsx(
              "flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl cursor-pointer transition-all",
              entityFile
                ? "border-indigo-500/50 bg-indigo-500/5"
                : "border-slate-700 hover:border-slate-600 bg-slate-800/50"
            )}
          >
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <Upload
                className={clsx(
                  "w-10 h-10 mb-3",
                  entityFile ? "text-indigo-400" : "text-slate-500"
                )}
              />
              <p className="mb-2 text-sm text-slate-300">
                <span className="font-semibold">Click para subir</span> o
                arrastra y suelta
              </p>
            </div>
            <input
              type="file"
              className="hidden"
              accept=".json,.yml,.yaml"
              onChange={(e) => handleFileChange(e, "entity")}
            />
          </label>

          {entityFile && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-300 truncate max-w-[200px]">
                  {entityFile.name}
                </span>
                <span className="text-indigo-400 font-medium">
                  {uploadProgress.entity}%
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress.entity}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-center pt-4">
        <button
          onClick={handleProcess}
          disabled={!rawFile || !entityFile || isProcessing}
          className={clsx(
            "flex items-center gap-3 px-10 py-4 rounded-xl font-bold text-lg transition-all shadow-lg",
            !rawFile || !entityFile || isProcessing
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
          Asegúrate de que el archivo de Raw Data (JSON o YAML) contenga el
          array de registros principal y el archivo de Entidades Conocidas
          (YAML) defina las entidades con sus respectivos identificadores
          únicos. El sistema validará la estructura antes de iniciar el análisis
          profundo.
        </div>
      </div>
    </div>
  );
};

export default IngestionView;
