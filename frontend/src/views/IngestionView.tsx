/**
 * Ingestion view component
 * Handles file uploads for extraction data and known entities
 * Implements the UI requirements with separate processes
 */

import React, { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  FileText, 
  Database, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  X,
  Layers,
  FileStack
} from 'lucide-react';
import { useIngestionStore, useNotificationStore } from '../store/useStore';
import { apiService } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import BulkFileUpload from '../components/BulkFileUpload';
import clsx from 'clsx';

type IngestionType = 'extraction_data' | 'known_entities';

const IngestionView: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { addNotification } = useNotificationStore();
  const { isUploading, setUploading, uploadProgress, setUploadProgress } = useIngestionStore();
  
  const [selectedType, setSelectedType] = useState<IngestionType>(
    (searchParams.get('type') as IngestionType) || 'extraction_data'
  );
  const [uploadMode, setUploadMode] = useState<'single' | 'bulk'>('single');
  const [formData, setFormData] = useState({
    publication: '',
    entityName: 'known_entities',
    dataPathDeltaLake: 'ship_entries',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);

  // Handle file drop
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      
      // Validate file type based on ingestion type
      const validExtensions = selectedType === 'extraction_data' 
        ? ['.json'] 
        : ['.yaml', '.yml'];
      
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      
      if (!validExtensions.includes(fileExtension)) {
        addNotification({
          type: 'error',
          title: 'Formato de archivo inválido',
          message: `Para ${selectedType === 'extraction_data' ? 'datos de extracción' : 'entidades conocidas'} se requiere formato ${validExtensions.join(' o ')}`
        });
        return;
      }
      
      setSelectedFile(file);
      setUploadResult(null);
    }
  }, [selectedType, addNotification]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: selectedType === 'extraction_data' 
      ? { 'application/json': ['.json'] }
      : { 'application/x-yaml': ['.yaml', '.yml'] }
  });

  const handleTypeChange = (type: IngestionType) => {
    setSelectedType(type);
    setSearchParams({ type });
    setSelectedFile(null);
    setUploadResult(null);
    setUploadMode('single'); // Reset to single mode when changing type
  };

  const handleModeChange = (mode: 'single' | 'bulk') => {
    setUploadMode(mode);
    setSelectedFile(null);
    setUploadResult(null);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      addNotification({
        type: 'error',
        title: 'Archivo requerido',
        message: 'Por favor selecciona un archivo para subir'
      });
      return;
    }

    if (selectedType === 'extraction_data' && !formData.publication) {
      addNotification({
        type: 'error',
        title: 'Publicación requerida',
        message: 'Por favor selecciona una publicación para los datos de extracción'
      });
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      setUploadResult(null);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev: number) => Math.min(prev + 10, 90));
      }, 200);

      const result = await apiService.uploadFile(
        selectedFile,
        selectedType,
        selectedType === 'extraction_data' ? formData.publication : undefined,
        selectedType === 'known_entities' ? formData.entityName : undefined,
        selectedType === 'extraction_data' ? formData.dataPathDeltaLake : undefined
      );

      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadResult(result);

      addNotification({
        type: 'success',
        title: 'Archivo subido exitosamente',
        message: `Se procesaron ${result.records_processed} registros`
      });

      // Reset form
      setTimeout(() => {
        setSelectedFile(null);
        setUploadProgress(0);
      }, 2000);

    } catch (error) {
      setUploadProgress(0);
      addNotification({
        type: 'error',
        title: 'Error al subir archivo',
        message: error instanceof Error ? error.message : 'Error desconocido'
      });
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setUploadResult(null);
  };

  const handleBulkUploadComplete = (stats: any) => {
    addNotification({
      type: 'success',
      title: 'Carga masiva completada',
      message: `Se procesaron ${stats.success} archivos exitosamente de ${stats.total} total. ${stats.totalRecordsProcessed} registros procesados.`
    });
  };

  const handleFileProcessed = (file: any) => {
    // Optional: Handle individual file completion
    console.log('Archivo procesado:', file.file.name);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Ingestión de Datos</h1>
        <p className="mt-1 text-sm text-gray-600">
          Sube archivos de datos de extracción o entidades conocidas al sistema
        </p>
      </div>

      {/* Type Selection */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Tipo de Ingestión</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => handleTypeChange('extraction_data')}
            className={clsx(
              'p-4 border-2 rounded-xl text-left transition-all duration-200',
              selectedType === 'extraction_data'
                ? 'border-blue-500 bg-blue-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
            )}
          >
            <div className="flex items-center">
              <FileText className={clsx(
                'w-6 h-6 mr-3',
                selectedType === 'extraction_data' ? 'text-blue-600' : 'text-gray-400'
              )} />
              <div>
                <h3 className="font-medium text-gray-900">Datos de Extracción</h3>
                <p className="text-sm text-gray-600">Archivos JSON con datos extraídos</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => handleTypeChange('known_entities')}
            className={clsx(
              'p-4 border-2 rounded-xl text-left transition-all duration-200',
              selectedType === 'known_entities'
                ? 'border-blue-500 bg-blue-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
            )}
          >
            <div className="flex items-center">
              <Database className={clsx(
                'w-6 h-6 mr-3',
                selectedType === 'known_entities' ? 'text-blue-600' : 'text-gray-400'
              )} />
              <div>
                <h3 className="font-medium text-gray-900">Entidades Conocidas</h3>
                <p className="text-sm text-gray-600">Archivos YAML con entidades</p>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Upload Mode Selection */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Modo de Carga</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => handleModeChange('single')}
            className={clsx(
              'p-4 border-2 rounded-xl text-left transition-all duration-200',
              uploadMode === 'single'
                ? 'border-blue-500 bg-blue-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
            )}
          >
            <div className="flex items-center">
              <FileText className={clsx(
                'w-6 h-6 mr-3',
                uploadMode === 'single' ? 'text-blue-600' : 'text-gray-400'
              )} />
              <div>
                <h3 className="font-medium text-gray-900">Archivo Individual</h3>
                <p className="text-sm text-gray-600">Sube un archivo a la vez</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => handleModeChange('bulk')}
            className={clsx(
              'p-4 border-2 rounded-xl text-left transition-all duration-200',
              uploadMode === 'bulk'
                ? 'border-blue-500 bg-blue-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
            )}
          >
            <div className="flex items-center">
              <FileStack className={clsx(
                'w-6 h-6 mr-3',
                uploadMode === 'bulk' ? 'text-blue-600' : 'text-gray-400'
              )} />
              <div>
                <h3 className="font-medium text-gray-900">Carga Masiva</h3>
                <p className="text-sm text-gray-600">Sube múltiples archivos (500+)</p>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Configuration Form */}
      {selectedType === 'extraction_data' && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Configuración de Extracción</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="publication" className="block text-sm font-medium text-gray-700 mb-2">
                Publicación *
              </label>
              <select
                id="publication"
                name="publication"
                value={formData.publication}
                onChange={handleInputChange}
                className="input"
                required
              >
                <option value="">Selecciona una publicación</option>
                <option value="db">Diario de Barcelona (DB)</option>
                <option value="dm">Diario de Madrid (DM)</option>
                <option value="sm">Semanario de Málaga (SM)</option>
              </select>
            </div>
            <div>
              <label htmlFor="dataPathDeltaLake" className="block text-sm font-medium text-gray-700 mb-2">
                Ruta en Delta Lake
              </label>
              <input
                type="text"
                id="dataPathDeltaLake"
                name="dataPathDeltaLake"
                value={formData.dataPathDeltaLake}
                onChange={handleInputChange}
                className="input"
                placeholder="ship_entries"
              />
            </div>
          </div>
        </div>
      )}

      {selectedType === 'known_entities' && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Configuración de Entidades</h2>
          <div>
            <label htmlFor="entityName" className="block text-sm font-medium text-gray-700 mb-2">
              Nombre de Entidad
            </label>
            <input
              type="text"
              id="entityName"
              name="entityName"
              value={formData.entityName}
              onChange={handleInputChange}
              className="input"
              placeholder="known_entities"
            />
          </div>
        </div>
      )}

      {/* File Upload */}
      {uploadMode === 'single' ? (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Subir Archivo Individual</h2>
          
          {!selectedFile ? (
            <div
              {...getRootProps()}
              className={clsx(
                'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200',
                isDragActive
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
              )}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'Suelta el archivo aquí' : 'Arrastra un archivo o haz clic para seleccionar'}
              </p>
              <p className="text-sm text-gray-600">
                Formato requerido: {selectedType === 'extraction_data' ? 'JSON' : 'YAML'}
              </p>
            </div>
          ) : (
            <div className="border border-gray-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <FileText className="w-8 h-8 text-blue-600 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">{selectedFile.name}</p>
                    <p className="text-sm text-gray-600">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={removeFile}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  disabled={isUploading}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Upload Progress */}
              {isUploading && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Subiendo archivo...</span>
                    <span className="text-sm text-gray-600">{uploadProgress}%</span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Upload Result */}
              {uploadResult && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-xl">
                  <div className="flex items-center">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-green-800">
                        Archivo procesado exitosamente
                      </p>
                      <p className="text-sm text-green-700">
                        {uploadResult.records_processed} registros procesados
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload Button */}
          {selectedFile && !uploadResult && (
            <div className="mt-4">
              <button
                onClick={handleUpload}
                disabled={isUploading || (selectedType === 'extraction_data' && !formData.publication)}
                className="btn btn-primary w-full"
              >
                {isUploading ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Subiendo archivo...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5 mr-2" />
                    Subir archivo
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Layers className="w-5 h-5 mr-2" />
            Carga Masiva de Archivos
          </h2>
          <p className="text-sm text-gray-600 mb-6">
            Sube múltiples archivos JSON simultáneamente. El sistema procesará hasta 500+ archivos 
            con procesamiento en paralelo y monitoreo en tiempo real.
          </p>
          
          <BulkFileUpload
            ingestionType={selectedType}
            publication={selectedType === 'extraction_data' ? formData.publication : undefined}
            entityName={selectedType === 'known_entities' ? formData.entityName : undefined}
            maxConcurrentUploads={5}
            maxRetries={3}
            onUploadComplete={handleBulkUploadComplete}
            onFileProcessed={handleFileProcessed}
          />
        </div>
      )}

      {/* Information */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Información Importante</h2>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
            <p>
              Los procesos de ingestión están separados para evitar conflictos. 
              Solo se puede procesar un tipo de archivo a la vez.
            </p>
          </div>
          <div className="flex items-start">
            <Clock className="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
            <p>
              El procesamiento es asíncrono. Recibirás una confirmación inmediata, 
              pero el procesamiento completo puede tomar algunos minutos.
            </p>
          </div>
          <div className="flex items-start">
            <FileText className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
            <p>
              Los archivos se almacenan temporalmente y se eliminan después del procesamiento.
            </p>
          </div>
          {uploadMode === 'bulk' && (
            <div className="flex items-start">
              <Layers className="w-5 h-5 text-purple-500 mr-2 mt-0.5 flex-shrink-0" />
              <p>
                <strong>Carga Masiva:</strong> Procesa hasta 5 archivos simultáneamente con reintentos automáticos. 
                Puedes pausar, reanudar y monitorear el progreso en tiempo real.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IngestionView;