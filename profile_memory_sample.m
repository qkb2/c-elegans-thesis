function prof = profile_memory_sample(prof)

    % Linux RSS (same idea as psutil rss)
    try
        status_file = sprintf('/proc/%d/status', prof.pid);

        fid = fopen(status_file, 'r');
        txt = fread(fid, '*char')';
        fclose(fid);

        token = regexp(txt, ...
            'VmRSS:\s+(\d+)\s+kB', ...
            'tokens', 'once');

        rss_mb = str2double(token{1}) / 1024;

        prof.max_ram_mb = max(prof.max_ram_mb, rss_mb);

    catch
    end

    % GPU memory (NVIDIA)
    try
        g = gpuDevice();

        gpu_mb = ...
            (g.TotalMemory - g.AvailableMemory) / 1024^2;

        prof.max_gpu_mb = max(prof.max_gpu_mb, gpu_mb);

    catch
    end
end