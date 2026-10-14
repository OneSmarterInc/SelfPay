require 'xcodeproj'
Dir.chdir(__dir__)
abort 'Invalid app configuration' unless system('python3', '../tools/generate_app_config.py', 'ios')
project = Xcodeproj::Project.new('MySelfPay.xcodeproj')
target = project.new_target(:application, 'MySelfPay', :ios, '15.0')
group = project.main_group.new_group('MySelfPay', 'MySelfPay')
Dir.glob('MySelfPay/*.swift').sort.each do |file|
  target.source_build_phase.add_file_reference(group.new_file(File.basename(file)))
end
target.resources_build_phase.add_file_reference(group.new_file('Assets.xcassets'))
group.new_file('Info.plist')
target.build_configurations.each do |config|
  config.build_settings.merge!({
    'PRODUCT_BUNDLE_IDENTIFIER' => 'com.onesmarter.myselfpay',
    'PRODUCT_NAME' => 'MySelfPay',
    'INFOPLIST_FILE' => 'MySelfPay/Info.plist',
    'SWIFT_VERSION' => '5.0',
    'TARGETED_DEVICE_FAMILY' => '1,2',
    'ASSETCATALOG_COMPILER_APPICON_NAME' => 'AppIcon',
    'CURRENT_PROJECT_VERSION' => ENV.fetch('BUILD_NUMBER', '1'),
    'CODE_SIGN_STYLE' => 'Manual',
    'SUPPORTS_MACCATALYST' => 'NO'
  })
end
project.save
scheme = Xcodeproj::XCScheme.new
scheme.add_build_target(target)
scheme.set_launch_target(target)
scheme.save_as('MySelfPay.xcodeproj', 'MySelfPay', true)
