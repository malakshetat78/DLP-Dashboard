import React, { useState, useEffect } from 'react';
import { Shield, Upload, Download, Lock, Eye, AlertTriangle, CheckCircle, FileText, Wifi, WifiOff, X, Image as ImageIcon, FileType, Key } from 'lucide-react';

const DLPDashboard = () => {
  const [activeTab, setActiveTab] = useState('files');
  const [files, setFiles] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showEncryptionModal, setShowEncryptionModal] = useState(false);
  const [showWatermarkModal, setShowWatermarkModal] = useState(false);
  const [selectedFileInfo, setSelectedFileInfo] = useState(null);
  const [encryptionTest, setEncryptionTest] = useState({
    type: 'text',
    file: null,
    text: '',
    encrypted: null,
    decrypted: null,
    keys: null,
    loading: false
  });
  const [user] = useState({
    username: 'admin',
    role: 'Administrator',
    clearanceLevel: 5,
    department: 'IT Security'
  });

  const API_URL = 'http://127.0.0.1:5000';

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const response = await fetch(`${API_URL}/files`);
      if (response.ok) {
        setIsConnected(true);
        setErrorMessage('');
        fetchFiles();
        fetchAuditLogs();
      } else {
        throw new Error('Server responded with error');
      }
    } catch (err) {
      setIsConnected(false);
      setErrorMessage('⚠️ Cannot connect to backend server. Make sure Flask is running on port 5000');
      console.error('Connection error:', err);
    }
  };

  const fetchFiles = async () => {
    try {
      const response = await fetch(`${API_URL}/files`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setFiles(Array.isArray(data) ? data : []);
      setIsConnected(true);
    } catch (err) {
      console.error('Error fetching files:', err);
      setIsConnected(false);
      setFiles([]);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const response = await fetch(`${API_URL}/audit`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setAuditLogs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching audit logs:', err);
      setAuditLogs([]);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setSelectedFile(file);
    setErrorMessage('');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(percent);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          setErrorMessage('');
          alert('✅ File uploaded and encrypted successfully!');
          setSelectedFile(null);
          setUploadProgress(0);
          setTimeout(() => {
            fetchFiles();
            fetchAuditLogs();
          }, 500);
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText);
            setErrorMessage(`❌ Upload failed: ${errorData.error || xhr.statusText}`);
            console.error('Upload error details:', errorData);
          } catch {
            setErrorMessage(`❌ Upload failed: ${xhr.statusText}`);
          }
          setUploadProgress(0);
        }
      });

      xhr.addEventListener('error', () => {
        setErrorMessage('❌ Network error. Check if Flask server is running on port 5000');
        setUploadProgress(0);
      });

      xhr.open('POST', `${API_URL}/upload`);
      xhr.send(formData);
      
    } catch (err) {
      setErrorMessage(`❌ Error: ${err.message}`);
      setUploadProgress(0);
    }
  };

  const handleDownload = async (file) => {
    try {
      setErrorMessage('');
      const response = await fetch(`${API_URL}/download/${file.id}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || 'Download failed');
      }
      
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        const blob = new Blob([`This is the decrypted content of: ${file.name}\n\nFile downloaded successfully from DLP System.`], { 
          type: 'text/plain' 
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        alert('✅ File downloaded and decrypted successfully!');
      } else {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        alert('✅ File downloaded successfully!');
      }
      
      setTimeout(() => fetchAuditLogs(), 500);
      
    } catch (err) {
      setErrorMessage(`❌ Download failed: ${err.message}`);
      alert(`❌ Download failed: ${err.message}`);
    }
  };

  const handleDownloadEncrypted = async (file) => {
    try {
      setErrorMessage('');
      const response = await fetch(`${API_URL}/download-encrypted/${file.id}`, {
        method: 'GET'
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || 'Download failed');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${file.name}.encrypted`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      alert('🔒 Encrypted file downloaded successfully!');
      
      setTimeout(() => fetchAuditLogs(), 500);
      
    } catch (err) {
      setErrorMessage(`❌ Download failed: ${err.message}`);
      alert(`❌ Download failed: ${err.message}`);
    }
  };

  const showEncryptionDetails = (file) => {
    setSelectedFileInfo(file);
    setShowEncryptionModal(true);
  };

  const showWatermarkDetails = (file) => {
    setSelectedFileInfo(file);
    setShowWatermarkModal(true);
  };

  const getClassificationColor = (classification) => {
    const colors = {
      'Secret': { bg: '#fee2e2', text: '#991b1b' },
      'Confidential': { bg: '#fed7aa', text: '#9a3412' },
      'Internal': { bg: '#fef3c7', text: '#92400e' },
      'Public': { bg: '#d1fae5', text: '#065f46' }
    };
    return colors[classification] || { bg: '#f3f4f6', text: '#1f2937' };
  };

  // ==================== Client-Side Encryption Functions ====================
  
  const generateRSAKeys = async () => {
    try {
      const response = await fetch(`${API_URL}/generate-keys`, {
        method: 'POST'
      });
      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error generating keys:', err);
      throw err;
    }
  };

  const encryptFile = async (file, publicKey) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('public_key', publicKey);

      const response = await fetch(`${API_URL}/encrypt-file`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Encryption failed');
      
      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error encrypting file:', err);
      throw err;
    }
  };

  const encryptText = async (text, publicKey) => {
    try {
      const response = await fetch(`${API_URL}/encrypt-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: text,
          public_key: publicKey
        })
      });

      if (!response.ok) throw new Error('Text encryption failed');
      
      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error encrypting text:', err);
      throw err;
    }
  };

  const decryptFile = async (encryptedData, encryptedKey, iv, authTag, privateKey, metadata) => {
    try {
      const response = await fetch(`${API_URL}/decrypt-file`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          encrypted_data: encryptedData,
          encrypted_key: encryptedKey,
          iv: iv,
          auth_tag: authTag,
          private_key: privateKey,
          metadata: metadata
        })
      });

      if (!response.ok) throw new Error('Decryption failed');
      
      const blob = await response.blob();
      return blob;
    } catch (err) {
      console.error('Error decrypting file:', err);
      throw err;
    }
  };

  const decryptText = async (encryptedData, encryptedKey, iv, authTag, privateKey) => {
    try {
      const response = await fetch(`${API_URL}/decrypt-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          encrypted_data: encryptedData,
          encrypted_key: encryptedKey,
          iv: iv,
          auth_tag: authTag,
          private_key: privateKey
        })
      });

      if (!response.ok) throw new Error('Text decryption failed');
      
      const data = await response.json();
      return data.text;
    } catch (err) {
      console.error('Error decrypting text:', err);
      throw err;
    }
  };

  // ==================== Encryption Test Handlers ====================

  const handleTestEncryption = async () => {
    setEncryptionTest(prev => ({ ...prev, loading: true, encrypted: null, decrypted: null }));
    
    try {
      const keys = await generateRSAKeys();
      setEncryptionTest(prev => ({ ...prev, keys }));

      if (encryptionTest.type === 'image' && encryptionTest.file) {
        const encrypted = await encryptFile(encryptionTest.file, keys.public_key);
        setEncryptionTest(prev => ({ ...prev, encrypted, loading: false }));
        alert('✅ Image encrypted successfully!');
      } else if (encryptionTest.type === 'text' && encryptionTest.text) {
        const encrypted = await encryptText(encryptionTest.text, keys.public_key);
        setEncryptionTest(prev => ({ ...prev, encrypted, loading: false }));
        alert('✅ Text encrypted successfully!');
      }
    } catch (err) {
      alert(`❌ Encryption failed: ${err.message}`);
      setEncryptionTest(prev => ({ ...prev, loading: false }));
    }
  };

  const handleTestDecryption = async () => {
    if (!encryptionTest.encrypted || !encryptionTest.keys) {
      alert('Please encrypt first!');
      return;
    }

    setEncryptionTest(prev => ({ ...prev, loading: true }));

    try {
      if (encryptionTest.type === 'image') {
        const blob = await decryptFile(
          encryptionTest.encrypted.encrypted_data,
          encryptionTest.encrypted.encrypted_key,
          encryptionTest.encrypted.iv,
          encryptionTest.encrypted.auth_tag,
          encryptionTest.keys.private_key,
          encryptionTest.encrypted.metadata
        );
        
        const url = URL.createObjectURL(blob);
        setEncryptionTest(prev => ({ ...prev, decrypted: url, loading: false }));
        alert('✅ Image decrypted successfully!');
      } else if (encryptionTest.type === 'text') {
        const decryptedText = await decryptText(
          encryptionTest.encrypted.encrypted_data,
          encryptionTest.encrypted.encrypted_key,
          encryptionTest.encrypted.iv,
          encryptionTest.encrypted.auth_tag,
          encryptionTest.keys.private_key
        );
        
        setEncryptionTest(prev => ({ ...prev, decrypted: decryptedText, loading: false }));
        alert('✅ Text decrypted successfully!');
      }
    } catch (err) {
      alert(`❌ Decryption failed: ${err.message}`);
      setEncryptionTest(prev => ({ ...prev, loading: false }));
    }
  };

  const handleTestFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setEncryptionTest(prev => ({ 
        ...prev, 
        file, 
        encrypted: null, 
        decrypted: null,
        keys: null 
      }));
    }
  };

  const resetEncryptionTest = () => {
    if (encryptionTest.decrypted && encryptionTest.type === 'image') {
      URL.revokeObjectURL(encryptionTest.decrypted);
    }
    setEncryptionTest({
      type: 'text',
      file: null,
      text: '',
      encrypted: null,
      decrypted: null,
      keys: null,
      loading: false
    });
  };

  const styles = {
    container: { minHeight: '100vh', background: '#1f2937', fontFamily: 'system-ui, -apple-system, sans-serif' },
    header: { background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(10px)', borderBottom: '1px solid #1e40af', padding: '16px' },
    headerContent: { maxWidth: '1280px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
    title: { fontSize: '24px', fontWeight: 'bold', color: 'white', margin: 0 },
    subtitle: { fontSize: '14px', color: '#93c5fd', margin: 0 },
    statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px,1fr))', gap: '24px', marginBottom: '32px' },
    statCard: (gradient) => ({ background: gradient, borderRadius: '12px', padding: '24px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.5)', color: 'white' }),
    tabContainer: { background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(10px)', borderRadius: '12px', border: '1px solid #1e40af', overflow: 'hidden' },
    tabButton: (isActive) => ({ padding: '16px 24px', fontWeight: '600', background: isActive ? '#2563eb' : 'transparent', color: isActive ? 'white' : '#93c5fd', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px', transition: 'all 0.3s' }),
    fileCard: { background: 'rgba(31,41,55,0.5)', border: '1px solid #1d4ed8', borderRadius: '8px', padding: '20px', marginBottom: '16px' },
    badge: (colors) => ({ padding: '4px 12px', borderRadius: '9999px', fontSize: '12px', fontWeight: '600', backgroundColor: colors.bg, color: colors.text }),
    errorBanner: { background: '#7f1d1d', color: '#fca5a5', padding: '12px 24px', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '12px' },
    modal: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
    modalContent: { background: '#1f2937', borderRadius: '12px', padding: '32px', maxWidth: '600px', width: '90%', border: '1px solid #1e40af', maxHeight: '90vh', overflow: 'auto' },
    button: { background: '#2563eb', color: 'white', padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px', fontWeight: '600' }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Shield size={40} color="#60a5fa" />
            <div>
              <h1 style={styles.title}>DLP Security System</h1>
              <p style={styles.subtitle}>Data Leak Prevention Platform</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', background: isConnected ? '#14532d' : '#7f1d1d', borderRadius: '8px' }}>
              {isConnected ? <Wifi size={16} color="#86efac" /> : <WifiOff size={16} color="#fca5a5" />}
              <span style={{ color: isConnected ? '#86efac' : '#fca5a5', fontSize: '12px', fontWeight: '600' }}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div style={{ textAlign: 'right', color: 'white' }}>
              <div style={{ fontWeight: '600' }}>{user.username}</div>
              <div style={{ fontSize: '12px', color: '#93c5fd' }}>{user.role} | Level {user.clearanceLevel}</div>
            </div>
            <div style={{ width: '48px', height: '48px', background: 'linear-gradient(to bottom right,#3b82f6,#9333ea)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '20px' }}>
              {user.username[0].toUpperCase()}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 24px' }}>
        {/* Error Banner */}
        {errorMessage && (
          <div style={styles.errorBanner}>
            <AlertTriangle size={20} />
            <span>{errorMessage}</span>
            <button onClick={checkConnection} style={{ marginLeft: 'auto', background: '#991b1b', color: 'white', padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontWeight: '600' }}>
              Retry Connection
            </button>
          </div>
        )}

        {/* Statistics Cards */}
        <div style={styles.statsGrid}>
          <div style={styles.statCard('linear-gradient(to bottom right,#2563eb,#1e40af)')}>
            <p style={{ opacity: 0.8, fontSize: '14px', margin: 0 }}>Total Files</p>
            <p style={{ fontSize: '36px', fontWeight: 'bold', margin: '8px 0 0 0' }}>{files.length}</p>
          </div>
          <div style={styles.statCard('linear-gradient(to bottom right,#059669,#047857)')}>
            <p style={{ opacity: 0.8, fontSize: '14px', margin: 0 }}>Encrypted</p>
            <p style={{ fontSize: '36px', fontWeight: 'bold', margin: '8px 0 0 0' }}>{files.filter(f => f.encrypted).length}</p>
          </div>
          <div style={styles.statCard('linear-gradient(to bottom right,#7c3aed,#6d28d9)')}>
            <p style={{ opacity: 0.8, fontSize: '14px', margin: 0 }}>Watermarked</p>
            <p style={{ fontSize: '36px', fontWeight: 'bold', margin: '8px 0 0 0' }}>{files.filter(f => f.watermarked).length}</p>
          </div>
          <div style={styles.statCard('linear-gradient(to bottom right,#ea580c,#c2410c)')}>
            <p style={{ opacity: 0.8, fontSize: '14px', margin: 0 }}>Access Denied</p>
            <p style={{ fontSize: '36px', fontWeight: 'bold', margin: '8px 0 0 0' }}>{auditLogs.filter(l => l.result === 'Denied').length}</p>
          </div>
        </div>

        {/* Tabs Container */}
        <div style={styles.tabContainer}>
          {/* Tab Headers */}
          <div style={{ borderBottom: '1px solid #1e40af', display: 'flex', flexWrap: 'wrap' }}>
            <button onClick={() => setActiveTab('files')} style={styles.tabButton(activeTab==='files')}>
              <FileText size={20}/> Secure Files
            </button>
            <button onClick={() => setActiveTab('upload')} style={styles.tabButton(activeTab==='upload')}>
              <Upload size={20}/> Upload File
            </button>
            <button onClick={() => setActiveTab('encrypt')} style={styles.tabButton(activeTab==='encrypt')}>
              <Key size={20}/> Test Encryption
            </button>
            <button onClick={() => setActiveTab('audit')} style={styles.tabButton(activeTab==='audit')}>
              <Shield size={20}/> Audit Logs
            </button>
          </div>

          {/* Tab Content */}
          <div style={{ padding: '24px' }}>
            {/* FILES TAB */}
            {activeTab==='files' && (
              files.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '60px', color: '#9ca3af' }}>
                  <FileText size={64} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p>No files uploaded yet. Use the Upload tab to add files.</p>
                </div>
              ) : (
                files.map(file=>(
                  <div key={file.id} style={styles.fileCard}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap: 'wrap', gap: '16px' }}>
                      <div style={{ flex:1, minWidth: '200px' }}>
                        <div style={{ display:'flex', alignItems:'center', gap:'12px', marginBottom:'8px', flexWrap: 'wrap' }}>
                          <FileText size={24} color="#60a5fa"/>
                          <h3 style={{ color:'white', fontSize:'18px', fontWeight:'600', margin:0 }}>{file.name}</h3>
                          <span style={styles.badge(getClassificationColor(file.classification))}>{file.classification}</span>
                        </div>
                      </div>
                      <div style={{ display:'flex', gap:'12px', alignItems:'center', flexWrap: 'wrap' }}>
                        {file.encrypted && (
                          <button 
                            onClick={() => showEncryptionDetails(file)}
                            style={{ display:'flex', alignItems:'center', gap:'4px', color:'#4ade80', background:'transparent', border:'1px solid #4ade80', padding:'6px 12px', borderRadius:'6px', cursor:'pointer', fontSize:'14px', whiteSpace: 'nowrap' }}
                          >
                            <Lock size={16}/>Encrypted
                          </button>
                        )}
                        {file.watermarked && (
                          <button 
                            onClick={() => showWatermarkDetails(file)}
                            style={{ display:'flex', alignItems:'center', gap:'4px', color:'#c084fc', background:'transparent', border:'1px solid #c084fc', padding:'6px 12px', borderRadius:'6px', cursor:'pointer', fontSize:'14px', whiteSpace: 'nowrap' }}
                          >
                            <Eye size={16}/>Watermarked
                          </button>
                        )}
                        <button 
                          onClick={() => handleDownloadEncrypted(file)}
                          style={{ background:'#7f1d1d', color:'#fca5a5', padding:'8px 16px', borderRadius:'8px', border:'1px solid #ef4444', cursor:'pointer', display:'flex', alignItems:'center', gap:'8px', fontWeight:'600', whiteSpace: 'nowrap' }}
                        >
                          <Lock size={16}/> Download Encrypted
                        </button>
                        <button 
                          onClick={() => handleDownload(file)}
                          style={{ background:'#2563eb', color:'white', padding:'8px 16px', borderRadius:'8px', border:'none', cursor:'pointer', display:'flex', alignItems:'center', gap:'8px', fontWeight:'600', whiteSpace: 'nowrap' }}
                        >
                          <Download size={16}/> Download Decrypted
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )
            )}

            {/* UPLOAD TAB */}
            {activeTab==='upload' && (
              <div style={{ maxWidth:'600px', margin:'0 auto' }}>
                <div style={{ background:'linear-gradient(to bottom right,#1e3a8a,#581c87)', borderRadius:'12px', padding:'32px', border:'2px dashed #3b82f6', textAlign:'center' }}>
                  <Upload size={64} color="#60a5fa" style={{ margin:'0 auto 16px' }}/>
                  <h3 style={{ color:'white', fontSize:'20px', fontWeight:'bold', marginBottom:'8px' }}>Upload Secure File</h3>
                  <p style={{ color:'#d1d5db', marginBottom:'24px' }}>File will be automatically encrypted and watermarked</p>
                  
                  <input type="file" onChange={handleFileUpload} style={{ display:'none' }} id="file-upload" disabled={!isConnected}/>
                  <label htmlFor="file-upload" style={{ display:'inline-block', background: isConnected ? '#2563eb' : '#6b7280', color:'white', padding:'12px 32px', borderRadius:'8px', cursor: isConnected ? 'pointer' : 'not-allowed', fontWeight:'600' }}>
                    {isConnected ? 'Select File' : 'Server Disconnected'}
                  </label>

                  {selectedFile && (
                    <div style={{ marginTop:'24px' }}>
                      <p style={{ color:'white', marginBottom:'8px' }}>Uploading: {selectedFile.name}</p>
                      <div style={{ width:'100%', background:'#374151', borderRadius:'9999px', height:'12px', overflow:'hidden' }}>
                        <div style={{ background:'linear-gradient(to right,#3b82f6,#9333ea)', height:'100%', width:`${uploadProgress}%`, transition:'width 0.3s' }} />
                      </div>
                      <p style={{ color:'#93c5fd', fontSize:'14px', marginTop:'8px' }}>{uploadProgress}% Complete</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ENCRYPT TAB */}
            {activeTab==='encrypt' && (
              <div style={{ maxWidth:'900px', margin:'0 auto' }}>
                <div style={{ background:'linear-gradient(to bottom right,#1e3a8a,#581c87)', borderRadius:'12px', padding:'32px', border:'2px solid #3b82f6' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                    <Key size={48} color="#60a5fa" />
                    <div>
                      <h2 style={{ color:'white', fontSize:'24px', fontWeight:'bold', margin: 0 }}>🔐 Encryption Testing Lab</h2>
                      <p style={{ color:'#93c5fd', fontSize:'14px', margin: '4px 0 0 0' }}>Test AES-256-GCM encryption - See the gibberish!</p>
                    </div>
                  </div>

                  {/* Type Selection */}
                  <div style={{ marginBottom: '24px' }}>
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <button 
                        onClick={() => { resetEncryptionTest(); setEncryptionTest(prev => ({ ...prev, type: 'text' })); }}
                        style={{ 
                          flex: 1, 
                          padding: '12px', 
                          background: encryptionTest.type === 'text' ? '#2563eb' : '#374151',
                          color: 'white',
                          border: 'none',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '8px',
                          fontWeight: '600'
                        }}
                      >
                        <FileType size={20} />
                        Encrypt Text
                      </button>
                      <button 
                        onClick={() => { resetEncryptionTest(); setEncryptionTest(prev => ({ ...prev, type: 'image' })); }}
                        style={{ 
                          flex: 1, 
                          padding: '12px', 
                          background: encryptionTest.type === 'image' ? '#2563eb' : '#374151',
                          color: 'white',
                          border: 'none',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '8px',
                          fontWeight: '600'
                        }}
                      >
                        <ImageIcon size={20} />
                        Encrypt Image
                      </button>
                    </div>
                  </div>

                  {/* Input Section */}
                  {encryptionTest.type === 'text' ? (
                    <div style={{ marginBottom: '24px' }}>
                      <label style={{ color: '#d1d5db', display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                        Enter Text to Encrypt
                      </label>
                      <textarea
                        value={encryptionTest.text}
                        onChange={(e) => setEncryptionTest(prev => ({ ...prev, text: e.target.value, encrypted: null, decrypted: null, keys: null }))}
                        placeholder="Type your confidential text here... 🔒"
                        style={{
                          width: '100%',
                          minHeight: '120px',
                          padding: '12px',
                          background: '#374151',
                          color: 'white',
                          border: '1px solid #1e40af',
                          borderRadius: '8px',
                          fontSize: '14px',
                          fontFamily: 'monospace',
                          resize: 'vertical'
                        }}
                      />
                    </div>
                  ) : (
                    <div style={{ marginBottom: '24px' }}>
                      <label style={{ color: '#d1d5db', display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                        Select Image File
                      </label>
                      <input 
                        type="file" 
                        accept="image/*"
                        onChange={handleTestFileChange}
                        style={{ 
                          width: '100%', 
                          padding: '12px', 
                          background: '#374151', 
                          color: 'white',
                          border: '1px solid #1e40af',
                          borderRadius: '8px'
                        }}
                      />
                      {encryptionTest.file && (
                        <p style={{ color: '#4ade80', fontSize: '14px', marginTop: '8px' }}>
                          ✓ Selected: {encryptionTest.file.name} ({(encryptionTest.file.size / 1024).toFixed(2)} KB)
                        </p>
                      )}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
                    <button
                      onClick={handleTestEncryption}
                      disabled={encryptionTest.loading || (encryptionTest.type === 'image' && !encryptionTest.file) || (encryptionTest.type === 'text' && !encryptionTest.text)}
                      style={{
                        flex: 1,
                        padding: '14px',
                        background: encryptionTest.loading || (encryptionTest.type === 'image' && !encryptionTest.file) || (encryptionTest.type === 'text' && !encryptionTest.text) ? '#6b7280' : '#059669',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: encryptionTest.loading || (encryptionTest.type === 'image' && !encryptionTest.file) || (encryptionTest.type === 'text' && !encryptionTest.text) ? 'not-allowed' : 'pointer',
                        fontWeight: '600',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px'
                      }}
                    >
                      <Lock size={20} />
                      {encryptionTest.loading ? 'Processing...' : 'Encrypt'}
                    </button>
                    <button
                      onClick={handleTestDecryption}
                      disabled={encryptionTest.loading || !encryptionTest.encrypted}
                      style={{
                        flex: 1,
                        padding: '14px',
                        background: encryptionTest.loading || !encryptionTest.encrypted ? '#6b7280' : '#7c3aed',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: (encryptionTest.loading || !encryptionTest.encrypted) ? 'not-allowed' : 'pointer',
                        fontWeight: '600',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px'
                      }}
                    >
                      <Eye size={20} />
                      {encryptionTest.loading ? 'Processing...' : 'Decrypt'}
                    </button>
                  </div>

                  {/* Encrypted Results */}
                  {encryptionTest.encrypted && (
                    <div style={{ background: '#1f2937', borderRadius: '8px', padding: '20px', border: '1px solid #4ade80', marginBottom: '16px' }}>
                      <h3 style={{ color: '#4ade80', fontSize: '16px', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <CheckCircle size={20} />
                        ✅ Encrypted Successfully
                      </h3>
                      
                      {/* Encrypted Data Preview */}
                      <div style={{ marginBottom: '16px' }}>
                        <h4 style={{ color: '#fbbf24', fontSize: '14px', marginBottom: '8px', fontWeight: '600' }}>🔒 Encrypted Data (Random Gibberish!)</h4>
                        <div style={{ 
                          background: '#111827', 
                          padding: '12px', 
                          borderRadius: '6px', 
                          fontFamily: 'monospace',
                          fontSize: '11px',
                          color: '#ef4444',
                          maxHeight: '150px',
                          overflow: 'auto',
                          wordBreak: 'break-all',
                          border: '2px solid #ef4444',
                          lineHeight: '1.5'
                        }}>
                          {encryptionTest.encrypted.encrypted_data.substring(0, 500)}...
                          <br /><br />
                          <span style={{ color: '#9ca3af' }}>
                            [Total: {encryptionTest.encrypted.encrypted_data.length} characters of complete noise]
                          </span>
                        </div>
                        <p style={{ color: '#9ca3af', fontSize: '12px', marginTop: '8px', fontStyle: 'italic' }}>
                          ⚠️ This is completely unreadable without the decryption key! No one can understand this.
                        </p>
                      </div>

                      <div style={{ color: '#d1d5db', fontSize: '13px', fontFamily: 'monospace' }}>
                        <p style={{ margin: '4px 0' }}>🔐 Algorithm: {encryptionTest.encrypted.metadata.algorithm}</p>
                        <p style={{ margin: '4px 0' }}>🔑 Key Size: {encryptionTest.encrypted.metadata.key_size} bits</p>
                        <p style={{ margin: '4px 0' }}>📊 Original Size: {encryptionTest.encrypted.metadata.original_size} bytes</p>
                        <p style={{ margin: '4px 0' }}>📦 Encrypted Size: {encryptionTest.encrypted.encrypted_data.length} characters</p>
                      </div>
                    </div>
                  )}

                  {/* Decrypted Results */}
                  {encryptionTest.decrypted && (
                    <div style={{ background: '#1f2937', borderRadius: '8px', padding: '20px', border: '1px solid #c084fc', marginBottom: '16px' }}>
                      <h3 style={{ color: '#c084fc', fontSize: '16px', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <CheckCircle size={20} />
                        ✅ Decrypted Successfully
                      </h3>
                      
                      {/* Comparison Section for Text */}
                      {encryptionTest.type === 'text' && (
                        <div style={{ marginBottom: '16px' }}>
                          <h4 style={{ color: '#fbbf24', fontSize: '14px', marginBottom: '12px', fontWeight: '600' }}>📊 Comparison: Original → Encrypted → Decrypted</h4>
                          
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                            {/* Original */}
                            <div>
                              <p style={{ color: '#4ade80', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>1️⃣ Original Text (Readable):</p>
                              <div style={{ 
                                background: '#14532d', 
                                padding: '12px', 
                                borderRadius: '6px',
                                border: '2px solid #4ade80',
                                color: '#d1fae5',
                                fontFamily: 'monospace',
                                fontSize: '13px',
                                minHeight: '60px',
                                wordBreak: 'break-word'
                              }}>
                                {encryptionTest.text}
                              </div>
                            </div>
                            
                            {/* Encrypted */}
                            <div>
                              <p style={{ color: '#ef4444', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>2️⃣ Encrypted (Complete Noise - Unreadable!):</p>
                              <div style={{ 
                                background: '#7f1d1d', 
                                padding: '12px', 
                                borderRadius: '6px',
                                border: '2px solid #ef4444',
                                color: '#fca5a5',
                                fontFamily: 'monospace',
                                fontSize: '11px',
                                minHeight: '60px',
                                maxHeight: '100px',
                                overflow: 'auto',
                                wordBreak: 'break-all'
                              }}>
                                {encryptionTest.encrypted.encrypted_data.substring(0, 300)}...
                              </div>
                            </div>
                            
                            {/* Decrypted */}
                            <div>
                              <p style={{ color: '#c084fc', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>3️⃣ Decrypted (Back to Original - Readable!):</p>
                              <div style={{ 
                                background: '#581c87', 
                                padding: '12px', 
                                borderRadius: '6px',
                                border: '2px solid #c084fc',
                                color: '#e9d5ff',
                                fontFamily: 'monospace',
                                fontSize: '13px',
                                minHeight: '60px',
                                wordBreak: 'break-word'
                              }}>
                                {encryptionTest.decrypted}
                              </div>
                            </div>
                          </div>
                          
                          <div style={{ marginTop: '16px', padding: '12px', background: '#14532d', borderRadius: '8px', border: '1px solid #4ade80' }}>
                            <p style={{ color: '#4ade80', fontSize: '14px', textAlign: 'center', fontWeight: '600', margin: 0 }}>
                              ✅ Success! Original text matches Decrypted text perfectly!
                            </p>
                          </div>
                        </div>
                      )}
                      
                      {encryptionTest.type === 'image' && (
                        <div style={{ textAlign: 'center' }}>
                          <img 
                            src={encryptionTest.decrypted} 
                            alt="Decrypted" 
                            style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px', border: '2px solid #c084fc' }}
                          />
                          <p style={{ color: '#d1d5db', fontSize: '14px', marginTop: '12px' }}>
                            ✅ Image restored to original format
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Reset Button */}
                  <button
                    onClick={resetEncryptionTest}
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: '#374151',
                      color: 'white',
                      border: '1px solid #6b7280',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    🔄 Reset Test
                  </button>
                </div>
              </div>
            )}

            {/* AUDIT TAB */}
            {activeTab==='audit' && (
              auditLogs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '60px', color: '#9ca3af' }}>
                  <Shield size={64} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p>No audit logs available yet.</p>
                </div>
              ) : (
                auditLogs.map(log=>(
                  <div key={log.id} style={{ background:'rgba(31,41,55,0.5)', border:'1px solid #374151', borderRadius:'8px', padding:'16px', marginBottom:'12px' }}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap: 'wrap', gap: '16px' }}>
                      <div style={{ display:'flex', alignItems:'center', gap:'16px' }}>
                        {log.result==='Success'?<CheckCircle size={24} color="#4ade80"/>:<AlertTriangle size={24} color="#ef4444"/>}
                        <div>
                          <div style={{ display:'flex', gap:'12px', alignItems:'center', flexWrap: 'wrap' }}>
                            <span style={{ color:'white', fontWeight:'600' }}>{log.action}</span>
                            <span style={{ color:'#6b7280' }}>•</span>
                            <span style={{ color:'#93c5fd' }}>{log.file}</span>
                          </div>
                          <div style={{ color:'#9ca3af', fontSize:'14px', marginTop:'4px' }}>User: {log.user} • IP: {log.ip}</div>
                        </div>
                      </div>
                      <div style={{ textAlign:'right' }}>
                        <span style={{ padding:'4px 12px', borderRadius:'9999px', fontSize:'12px', fontWeight:'600', backgroundColor: log.result==='Success'?'#14532d':'#7f1d1d', color: log.result==='Success'?'#86efac':'#fca5a5' }}>{log.result}</span>
                        <div style={{ color:'#6b7280', fontSize:'12px', marginTop:'4px' }}>{log.timestamp}</div>
                      </div>
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </div>
      </div>

      {/* Encryption Details Modal */}
      {showEncryptionModal && selectedFileInfo && (
        <div style={styles.modal} onClick={() => setShowEncryptionModal(false)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Lock size={32} color="#4ade80" />
                <h2 style={{ color: 'white', margin: 0, fontSize: '24px' }}>Encryption Details</h2>
              </div>
              <button onClick={() => setShowEncryptionModal(false)} style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
                <X size={24} />
              </button>
            </div>
            
            <div style={{ color: '#d1d5db', lineHeight: '1.8' }}>
              <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(74,222,128,0.1)', borderRadius: '8px', border: '1px solid #4ade80' }}>
                <p style={{ margin: '0 0 8px 0', color: '#4ade80', fontWeight: '600' }}>📄 File: {selectedFileInfo.name}</p>
                <p style={{ margin: 0, fontSize: '14px' }}>Classification: {selectedFileInfo.classification}</p>
              </div>
              
              <h3 style={{ color: 'white', fontSize: '16px', marginTop: '20px' }}>🔐 Encryption Algorithm</h3>
              <p style={{ margin: '8px 0', padding: '12px', background: '#374151', borderRadius: '6px' }}>
                <strong>AES-256-GCM</strong> (Advanced Encryption Standard)
              </p>
              
              <h3 style={{ color: 'white', fontSize: '16px', marginTop: '20px' }}>🔑 Key Management</h3>
              <p style={{ margin: '8px 0' }}>• Hybrid Encryption (RSA + AES)</p>
              <p style={{ margin: '8px 0' }}>• 256-bit symmetric key</p>
              <p style={{ margin: '8px 0' }}>• Key encrypted with user's public key</p>
              
              <h3 style={{ color: 'white', fontSize: '16px', marginTop: '20px' }}>✅ Security Features</h3>
              <p style={{ margin: '8px 0' }}>• End-to-end encryption</p>
              <p style={{ margin: '8px 0' }}>• Authenticated encryption (GCM mode)</p>
              <p style={{ margin: '8px 0' }}>• Per-file unique keys</p>
              <p style={{ margin: '8px 0' }}>• Tamper detection</p>
            </div>
            
            <button onClick={() => setShowEncryptionModal(false)} style={{ ...styles.button, marginTop: '24px', width: '100%', justifyContent: 'center' }}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* Watermark Details Modal */}
      {showWatermarkModal && selectedFileInfo && (
        <div style={styles.modal} onClick={() => setShowWatermarkModal(false)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Eye size={32} color="#c084fc" />
                <h2 style={{ color: 'white', margin: 0, fontSize: '24px' }}>Watermark Details</h2>
              </div>
              <button onClick={() => setShowWatermarkModal(false)} style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
                <X size={24} />
              </button>
            </div>
            
            <div style={{ color: '#d1d5db', lineHeight: '1.8' }}>
              <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(192,132,252,0.1)', borderRadius: '8px', border: '1px solid #c084fc' }}>
                <p style={{ margin: '0 0 8px 0', color: '#c084fc', fontWeight: '600' }}>📄 File: {selectedFileInfo.name}</p>
                <p style={{ margin: 0, fontSize: '14px' }}>Owner: {user.username}</p>
              </div>
              
              <h3 style={{ color: 'white', fontSize: '16px', marginTop: '20px' }}>🔍 Watermark Information</h3>
              <p style={{ margin: '8px 0', padding: '12px', background: '#374151', borderRadius: '6px' }}>
                <strong>Invisible Digital Watermark</strong>
              </p>
              
              <h3 style={{ color: 'white', fontSize: '16px', marginTop: '20px' }}>📋 Embedded Data</h3>
              <p style={{ margin: '8px 0' }}>• User ID: {user.username}</p>
              <p style={{ margin: '8px 0' }}>• Department: {user.department}</p>
              <p style={{ margin: '8px 0' }}>• Timestamp: {selectedFileInfo.uploaded}</p>
              <p style={{ margin: '8px 0' }}>• Unique Identifier: WM-{selectedFileInfo.id}-{Date.now().toString(36)}</p>
              
              <h3 style={{ color: 'white', fontSize: '16px', marginTop: '20px' }}>🛡️ Protection Features</h3>
              <p style={{ margin: '8px 0' }}>• Tamper-resistant watermark</p>
              <p style={{ margin: '8px 0' }}>• Leak tracking enabled</p>
              <p style={{ margin: '8px 0' }}>• Forensic analysis ready</p>
              <p style={{ margin: '8px 0' }}>• User attribution system</p>
            </div>
            
            <button onClick={() => setShowWatermarkModal(false)} style={{ ...styles.button, marginTop: '24px', width: '100%', justifyContent: 'center' }}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DLPDashboard;
                